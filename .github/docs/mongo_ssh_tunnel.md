1. If you haven't already, [set up MFA on your NERSC account](https://docs.nersc.gov/connect/mfa/)
   (it's required for SSHing in).
1. Run the following SSH tunneling command, substituting your actual NERSC username:

   ```ssh -L 127.0.0.1:27027:mongo-loadbalancer.nmdc-runtime-dev.development.svc.spin.nersc.org:27017 <YOUR_NERSC_USERNAME>@dtn01.nersc.gov '/bin/bash -c "while [[ 1 ]]; do echo heartbeat; sleep 300; done"'```

1. When prompted, provide your NERSC password concatenated with your MFA OTP code.
