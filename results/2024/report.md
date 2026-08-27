# Strommodell report

- Data year: 2024
- Source: energy-charts
- Resolution: 15 minutes
- Capacity rule: mean of 31 December capacity in previous and data year
- Battery efficiencies: charge 0.9, discharge 0.9

| scenario | pv_gw | wind_onshore_gw | wind_offshore_gw | battery_power_gw | battery_energy_gwh | gas_power_gw | gas_work_twh | curtailment_twh | battery_throughput_gwh | battery_final_soc_gwh | demand_peak_gw | unserved_load_twh |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0-iststand-2024 | 99.3 | 63.53 | 9.215 | 12.67 | 18.649999999792 | 163.33057515959143 | 895.9935833485389 | 0.0 | 8.392499999906402 | 0.0 | 179.03944533939074 | 0.0 |
| A-knapp | 300.0 | 250.0 | 70.0 | 50.0 | 200.0 | 156.72788039838628 | 319.433825575956 | 56.911425523505216 | 41979.23877389398 | 73.946359674174 | 179.03944533939074 | 0.0 |
| B-referenz | 400.0 | 300.0 | 80.0 | 100.0 | 400.0 | 156.6224631916004 | 214.15427165372446 | 127.48336434755286 | 105110.81406369389 | 400.0 | 179.03944533939074 | 0.0 |
| C-viel-ueberschuss | 500.0 | 350.0 | 100.0 | 150.0 | 600.0 | 156.51591527472857 | 133.378490966423 | 253.3060401536411 | 153165.0089420213 | 600.0 | 179.03944533939074 | 0.0 |
