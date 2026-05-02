#!/usr/bin/env bash
# Inspect MSRs and kernel state related to HFI/Thread Director activation.
set -u

echo "=== MSR inspection ==="
echo "IA32_HW_FEEDBACK_PTR    (0x17D0): nonzero if kernel allocated the feedback table"
sudo rdmsr -p 0  0x17D0 2>&1 | sed 's/^/  cpu 0  (P) : 0x/'
sudo rdmsr -p 6  0x17D0 2>&1 | sed 's/^/  cpu 6  (E) : 0x/'
sudo rdmsr -p 14 0x17D0 2>&1 | sed 's/^/  cpu 14 (LPE): 0x/'

echo ""
echo "IA32_HW_FEEDBACK_CONFIG (0x17D1): bit 0 = HFI enabled, bit 1 = ITD enabled"
sudo rdmsr -p 0  0x17D1 2>&1 | sed 's/^/  cpu 0  (P) : 0x/'
sudo rdmsr -p 6  0x17D1 2>&1 | sed 's/^/  cpu 6  (E) : 0x/'
sudo rdmsr -p 14 0x17D1 2>&1 | sed 's/^/  cpu 14 (LPE): 0x/'

echo ""
echo "IA32_PACKAGE_THERM_STATUS (0x1B1)"
sudo rdmsr -p 0 0x1B1 2>&1 | sed 's/^/  cpu 0 : 0x/'

echo ""
echo "=== CPUID 0x06 EDX (bit 19 = HFI, bit 23 = ITD) ==="
if command -v cpuid >/dev/null; then
  sudo cpuid -1 -r -l 0x06 2>&1 | grep -A1 "0x00000006 0x00:" | tail -1
else
  echo "  (cpuid not installed; sudo dnf install -y cpuid)"
fi

echo ""
echo "=== Kernel HFI driver state ==="
echo "- Loaded HFI module:"
lsmod | grep -i hfi || echo "  (no hfi module loaded)"
echo ""
echo "- dmesg HFI / Thread Director / hardware feedback entries:"
sudo dmesg 2>/dev/null | grep -iE 'hfi|thread.director|hardware.feedback|intel_hfi' | head -20
if [ $? -ne 0 ] || ! sudo dmesg 2>/dev/null | grep -qiE 'hfi|thread.director|hardware.feedback|intel_hfi'; then
  echo "  (no relevant dmesg lines found)"
fi

echo ""
echo "- Thermal/HFI sysfs entries:"
ls -la /sys/class/thermal/ 2>/dev/null | grep -iE 'hfi|thermal_zone' | head -10

echo ""
echo "- Kernel config for HFI:"
if [ -f /boot/config-$(uname -r) ]; then
  grep -iE 'intel_hfi|hfi_thermal|sched_thermal' /boot/config-$(uname -r) || \
    echo "  (no HFI config entries found)"
fi

echo ""
echo "=== Scheduler awareness of HFI ==="
echo "- /sys/kernel/debug/sched/features (HFI-related flags):"
sudo cat /sys/kernel/debug/sched/features 2>/dev/null | tr ' ' '\n' | grep -iE 'hfi|hybrid|asym|itd' || \
  echo "  (no HFI-related sched features visible)"

echo ""
echo "- intel_pstate / HWP status:"
cat /sys/devices/system/cpu/intel_pstate/status 2>/dev/null || echo "  (intel_pstate/status unavailable)"
