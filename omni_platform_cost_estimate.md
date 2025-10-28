# Omni Platform Cost Estimate on the Web (GCP)

Based on the deployment scripts, the Omni Platform can be deployed on Google Cloud Platform (GCP) using Compute Engine instances.

## Assumed Configuration
- Two Compute Engine instances: `omni-cpu-optimized` and `omni-storage-node`
- Machine type: n1-standard-4 (4 vCPUs, 15 GB RAM) for each (common for such setups)
- Region: us-central1 (as per script)
- Persistent disk: 100 GB standard per instance
- Additional services: MongoDB, Redis, Nginx (included in instance cost)
- Network: Minimal egress assumed

## Cost Breakdown (Monthly Estimate)
- **Compute Instances**: 2 x n1-standard-4 @ $0.0475/hour = $0.095/hour = $68.40/month
- **Persistent Disks**: 2 x 100 GB @ $0.04/GB/month = $8.00/month
- **Network Egress**: Assuming low usage, ~$1.00/month (varies)
- **Other**: IP addresses, load balancing if applicable, negligible for basic setup

## Total Estimated Monthly Cost: ~$77.40

**Note**: Actual costs depend on exact machine types, usage, and additional services. Use the GCP Pricing Calculator for precise estimates. For Render deployment, the starter plan is free for personal use, but production may incur fees.

## Recommendations
- Monitor usage with `gcloud billing accounts projects list`
- Optimize by using preemptible instances if suitable
- Consider sustained use discounts for long-term
