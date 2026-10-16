# Security Architecture & Best Practices

## 1. Principle of Least Privilege (PoLP)

Security is integrated across the application container, Kubernetes runtime, and AWS cloud boundary.

---

## 2. Infrastructure & Cloud Security

### 2.1 AWS IAM Roles for Service Accounts (IRSA)
* Instead of mounting static AWS credentials or giving EC2 node instance profiles broad permissions, we configure an **OIDC Identity Provider** on the EKS cluster.
* Kubernetes ServiceAccounts assume scoped IAM roles via STS AssumeRoleWithWebIdentity, receiving short-lived (1 hour) temporary tokens automatically injected by the EKS Pod Identity Webhook.

### 2.2 Network Security
* EKS worker nodes and application pods run exclusively inside **private subnets**.
* Ingress into the cluster is strictly restricted through the NGINX Ingress Controller residing in public subnets.
* Security groups enforce mutual isolation between the EKS Control Plane and worker node overlay networks.

---

## 3. Container & Runtime Hardening

### 3.1 Non-Root Execution
* Containers run as explicit non-root user `appuser` (UID: `10001`, GID: `10001`).
* Kubernetes securityContext enforces:
  ```yaml
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
  ```
* In the event of an application vulnerability or remote execution attempt, the attacker cannot modify system binaries or escape the container namespace.

### 3.2 Vulnerability Scanning in CI
* **Trivy Scanner:** Automated in the GitHub Actions pipeline to scan both repository filesystem dependencies and the final built Docker image before publishing to ECR.
* **Amazon ECR Enhanced Scanning:** `scan_on_push = true` automatically flags CVEs in published container layers.

---

## 4. Application Safeguards: Chaos Endpoint Protection
The failure-injection endpoints (`/api/simulate/failure` and `/api/simulate/latency`) present a potential denial-of-service risk if exposed to unauthorized users.
They are hardened with a dual defense:
1. **Environment Flag:** `SIMULATION_ENABLED` must be explicitly set to `true`. In production, default is `false`, returning an instant `403 Forbidden`.
2. **Secret Token Header:** Even when enabled, requests require the `X-Simulation-Token` header, returning `401 Unauthorized` on missing or incorrect tokens.
