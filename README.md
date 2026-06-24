# Investigating Task Scheduling on Intel's Three-Tier Arrow Lake-H


## Reproducing
Requries:
- Fedora 43 Workstation with kernel 6.17.1-300.fc43.x86_64
- gcc 15.2.1
On the reference hardware, after a fresh boot:

```bash
./scripts/pin_system.sh            # one-time per boot
./scripts/prep_session.sh         
./scripts/pass_A_stream_1t.sh     
./scripts/pass_B_stream_full.sh   
systemd-inhibit --what=sleep:idle:handle-lid-switch --who=arrowlake-bench --why="NPB 1-thread" \
  ./scripts/pass_C_npb_1t.sh      
systemd-inhibit --what=sleep:idle:handle-lid-switch --who=arrowlake-bench --why="NPB full-tier" \
  ./scripts/pass_D_npb_full.sh    
./scripts/aggregate.py            
```

