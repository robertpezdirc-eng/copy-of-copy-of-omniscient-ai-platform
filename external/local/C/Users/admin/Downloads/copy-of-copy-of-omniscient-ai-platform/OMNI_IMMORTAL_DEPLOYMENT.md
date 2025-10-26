# OMNI Immortal Platform - GCE Deployment Guide

## Architecture Overview

The OMNI platform runs in "Immortal Mode" with:
- **Dual instances**: v1 (active) and v2 (upgrade)
- **Zero downtime**: Automatic failover and hot upgrades
- **Checkpoint system**: Regular state snapshots for rollback
- **Watchdog monitoring**: Continuous health checks

## Quick Deployment

### 1. Deploy to GCE
```bash
# Make scripts executable
chmod +x omni_gce_deploy.sh
chmod +x omni_watchdog.sh

# Deploy to GCE
./omni_gce_deploy.sh your-project-id your-zone your-instance-name
```

### 2. Manual Setup (if needed)
```bash
# Copy files to instance
gcloud compute scp --recurse . your-instance:/opt/omni/ --zone=your-zone

# SSH and run setup
gcloud compute ssh your-instance --zone=your-zone
sudo /opt/omni/gce_setup.sh
```

### 3. Start Services
```bash
# Enable and start services
sudo systemctl enable omni-autolearn-v1
sudo systemctl start omni-autolearn-v1
sudo systemctl enable omni-immortal-watchdog
sudo systemctl start omni-immortal-watchdog

# Set up cron for watchdog
sudo crontab -e
# Add: */1 * * * * /opt/omni/omni_watchdog.sh
```

## Operations

### Health Monitoring
```bash
# Check service status
sudo systemctl status omni-autolearn-v1
sudo systemctl status omni-autolearn-v2
sudo systemctl status omni-immortal-watchdog

# Check logs
sudo journalctl -u omni-autolearn-v1 -f
sudo journalctl -u omni-immortal-watchdog -f
```

### Hot Upgrade
```bash
# Deploy new version to v2
./omni_hot_upgrade.sh /path/to/new/version

# System automatically switches when v2 is healthy
```

### Rollback
```bash
# Rollback to v1
./omni_rollback.sh v1

# Or rollback to v2
./omni_rollback.sh v2
```

### Manual Instance Control
```bash
# Start/stop instances
sudo systemctl start omni-autolearn-v1
sudo systemctl stop omni-autolearn-v2

# Check instance health
python /opt/omni/omni_immortal_watchdog.py health
```

## Monitoring

### Logs
- **Application logs**: `/var/log/omni_*.log`
- **System logs**: `sudo journalctl -u omni-*`
- **Watchdog logs**: `/var/log/omni_watchdog.log`

### Metrics
- **Active instance**: Check `/opt/omni/immortal_config.json`
- **Checkpoints**: List `/opt/omni/checkpoints/`
- **GCS uploads**: Check `gs://omni-meta-data/models/`

## Troubleshooting

### Common Issues

1. **Instance won't start**
   - Check logs: `sudo journalctl -u omni-autolearn-v1 --no-pager`
   - Verify Python environment: `/opt/omni/omni_env/bin/python --version`
   - Check file permissions: `ls -la /opt/omni/`

2. **VR connection fails**
   - Check port availability: `ss -ln | grep :9090`
   - Verify firewall rules
   - Test with: `python /opt/omni/simulate_vr_headset.py`

3. **GCS upload fails**
   - Check credentials: `gcloud auth list`
   - Verify bucket: `gsutil ls gs://omni-meta-data/`
   - Check permissions

4. **Watchdog not working**
   - Check cron: `crontab -l`
   - Verify script: `bash -n /opt/omni/omni_watchdog.sh`
   - Manual test: `/opt/omni/omni_watchdog.sh`

### Emergency Procedures

1. **Force restart all services**
   ```bash
   sudo systemctl stop omni-autolearn-v1 omni-autolearn-v2
   sudo systemctl stop omni-immortal-watchdog
   sudo systemctl start omni-autolearn-v1
   sudo systemctl start omni-immortal-watchdog
   ```

2. **Manual failover**
   ```bash
   python /opt/omni/omni_immortal_watchdog.py switch v2
   ```

3. **Restore from checkpoint**
   ```bash
   # Copy latest checkpoint files
   cp /opt/omni/checkpoints/latest_learn_summary.json ./learn_summary.json
   ```

## Security

- **Firewall**: Allow UDP port 9090-9091 for VR data
- **IAM**: Service account with GCS access
- **Updates**: Regular security patches via COS

## Performance

- **Resource monitoring**: Use Google Cloud Monitoring
- **Auto-scaling**: Configure based on load
- **Cost optimization**: Use preemptible instances for non-critical workloads
