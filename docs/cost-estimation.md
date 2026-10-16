# AWS Cost Estimation & Teardown Guide

## 1. Itemized Cost Breakdown (us-east-1)

| AWS Resource | Standard Production Setup | Our Lab-Optimized Setup | Monthly Cost (Lab) | Active Testing Cost (4 Hours) |
| :--- | :--- | :--- | :--- | :--- |
| **EKS Control Plane** | $\$0.10/\text{hr}$ | $\$0.10/\text{hr}$ | $\$73.00$ | $\$0.40$ |
| **NAT Gateway** | 3x AZs ($\$97.20/\text{mo}$) | **1x Single NAT** ($\$0.045/\text{hr}$) | $\$32.40$ | $\$0.18$ |
| **EC2 Managed Nodes** | $3\times\text{m5.large}$ ($\$210/\text{mo}$) | **$2\times\text{t3.medium}$** ($\$0.0416/\text{hr}\times 2$) | $\$60.00$ | $\$0.33$ |
| **Application Load Balancer** | $\$0.0225/\text{hr}$ | $\$0.0225/\text{hr}$ | $\$16.20$ | $\$0.09$ |
| **Amazon ECR Storage** | Negligible ($< 1\text{GB}$) | Negligible ($< 1\text{GB}$) | $<\$0.10$ | $<\$0.01$ |
| **Total Estimated Cost** | $\approx \$396.50/\text{month}$ | **$\approx \$181.70/\text{month}$** | **$\approx \$181.70$** | **$\approx \$1.00$** |

> [!TIP]
> **Key Optimization:** By configuring a single NAT gateway instead of one per AZ in `terraform/main.tf`, we cut networking costs by over 66% while maintaining full private-subnet security.

---

## 2. Resource Lifecycle Management

Because cloud testing costs accumulate hourly, never leave the EKS cluster running when you are not actively testing.

### Teardown Runbook
When your testing or demonstration session is complete, run:

```bash
cd terraform

# 1. Preview resources to be destroyed
terraform plan -destroy

# 2. Execute teardown
terraform destroy -auto-approve
```

### Verification After Teardown
Check AWS Console or run AWS CLI to ensure no lingering resources:
```bash
aws eks list-clusters --region us-east-1
aws ec2 describe-nat-gateways --filter "Name=state,Values=available" --region us-east-1
aws elbv2 describe-load-balancers --region us-east-1
```
Total lingering cost after running `terraform destroy` is $\$0.00$.
