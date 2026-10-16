# Interview Guide: Technical Q&A, Elevator Pitch, Resume & LinkedIn

## 1. The Two-Minute Interview Elevator Pitch

> "In this project, I built a cloud-native **Progressive Delivery Platform** on AWS EKS to solve a critical production problem: how to release microservices with true zero downtime while protecting users from bad deployments without manual monitoring.
>
> Standard Kubernetes rolling updates have a major limitation—if a new release contains a subtle error rate or latency regression, it gradually rolls out to 100% of pods and impacts all users before an engineer notices.
>
> To solve this, I architected an automated deployment platform using **Argo Rollouts**, **NGINX Ingress Controller**, and **Prometheus**. Instead of crude replica-based distribution, I integrated L7 traffic shifting to direct precise, weighted percentages—10%, 25%, 50%—to the canary version.
>
> During each stage, Argo Rollouts executes automated **Prometheus AnalysisTemplates** querying HTTP 5xx error rates and p95 latency percentiles. If error rates exceed 2% or p95 latency spikes above 400ms, the controller automatically aborts the rollout, reverts Ingress traffic to 0% in under 2 seconds, and leaves the stable release serving users uninterrupted.
>
> I provisioned the complete infrastructure—VPC, private subnets, managed node groups, and ECR—using **Terraform**, optimized costs by 66% using a single NAT gateway for lab environments, and verified availability using custom load testing scripts."

---

## 2. ATS-Friendly Resume Bullets

Copy and adapt these bullet points for your **Junior DevOps Engineer**, **Cloud Engineer**, or **Platform Engineer** resume:

* **Progressive Delivery Platform (Kubernetes, AWS EKS, Argo Rollouts, Terraform, Prometheus)**
  * Architected a zero-downtime deployment platform on AWS EKS utilizing **Argo Rollouts** and **NGINX Ingress** to implement automated canary and blue-green releases with dynamic L7 weighted traffic shifting (10% $\to$ 100%).
  * Automated release quality gates using **Prometheus AnalysisTemplates**, evaluating HTTP 5xx error rates and p95 latency percentiles to trigger autonomous rollbacks in $<25$ seconds upon SLO violations.
  * Authored modular **Terraform** configurations to provision an EKS cluster, managed node groups in private subnets, IAM OIDC roles for service accounts (IRSA), and ECR repositories, reducing lab networking costs by 66% with single NAT gateway architecture.
  * Built and containerized a high-performance **Python FastAPI** application with custom Prometheus metrics, non-root security context (UID 10001), and graceful shutdown handling.
  * Designed end-to-end **CI/CD pipeline** with GitHub Actions featuring automated linting, unit testing (pytest), Trivy container vulnerability scanning, and immutable image tagging.
  * Executed comprehensive chaos testing and load generation scripts, measuring and verifying 99.85% request availability and zero user-facing downtime during live release aborts.

---

## 3. LinkedIn Post Draft

```markdown
🚀 Excited to share my latest Cloud & DevOps project: Progressive Delivery Platform on AWS EKS!

Traditional Kubernetes rolling updates often release bugs to 100% of users before someone spots an alert. I wanted to build a platform that automates release verification using real-time observability.

Key Architectural Highlights:
🔹 Canary & Blue-Green Releases: Implemented Argo Rollouts integrated with NGINX Ingress Controller for fine-grained L7 traffic shifting (10% → 25% → 50% → 100%).
🔹 Automated Metric Analysis: Configured Prometheus PromQL gates monitoring HTTP 5xx error rates and p95 latency thresholds.
🔹 Zero-Touch Automated Rollback: If a release violates our SLO (<2% errors, <400ms latency), the system automatically aborts the rollout and restores stable traffic in seconds.
🔹 Infrastructure as Code: Provisioned VPC, private subnets, IAM IRSA, ECR, and EKS using modular Terraform with cost-optimized networking.
🔹 Container Security: Multi-stage Docker build running as a non-privileged user (UID 10001) with automated Trivy vulnerability scans in GitHub Actions.

Check out the full repository, architecture diagrams, and runbooks here: [GitHub Link]

#DevOps #Kubernetes #AWS #EKS #ArgoRollouts #Terraform #Prometheus #SRE #CloudEngineering
```

---

## 4. Technical Interview Questions & High-Scoring Answers

### Q1: Why use Progressive Delivery over traditional Deployment Rolling Updates?
**Answer:** A standard Kubernetes `Deployment` performs rolling updates by replacing old pods with new pods incrementally. However, it only verifies **pod readiness** (i.e., whether the container started and responded to a probe), not **application health or business logic correctness**. If a new version returns 500 errors or has a memory leak, the rolling update will still proceed to 100% completion. Progressive Delivery decouples deployment from release, exposing changes to a small canary percentage and continuously testing real telemetry against SLOs before advancing.

### Q2: Blue-Green versus Canary: How do they differ and when would you choose which?
**Answer:** 
* **Blue-Green:** Runs two full, identical environments (`active` and `preview`). Once preview passes smoke tests, traffic switches 100% instantaneously via service selectors. It is ideal when changes are incompatible (e.g., non-backward-compatible database schema migrations) and you can afford $2\times$ resource overhead during releases.
* **Canary:** Slowly exposes a small slice of live user traffic (e.g., 10%) to the new version alongside stable pods. It has minimal resource overhead and gives empirical proof of performance under real user workloads.

### Q3: Why does replica-based traffic routing differ from true weighted traffic splitting?
**Answer:** Without an L7 traffic router, a standard Kubernetes `Service` splits traffic strictly based on the ratio of backend pod endpoints in `kube-proxy`. If you have 4 pods, 1 canary pod is $25\%$ of traffic—you cannot achieve a 5% or 10% canary. Additionally, connection reuse (HTTP Keep-Alive / HTTP/2) pins connections to existing pods. By integrating Argo Rollouts with NGINX Ingress, traffic splitting occurs at the HTTP request layer via Lua headers, allowing exact 10% or 25% splitting regardless of replica counts.

### Q4: How does Argo Rollouts interact with Prometheus to trigger an automated rollback?
**Answer:** Argo Rollouts uses an `AnalysisTemplate` resource that defines PromQL queries, execution intervals, and success conditions. When a rollout advances to an analysis step, the controller initiates an `AnalysisRun`. It queries the Prometheus HTTP API (e.g., measuring the ratio of 5xx status codes over a 2-minute sliding window). If the metric breaches the threshold beyond the `failureLimit`, the `AnalysisRun` status changes to `Failed`. The Argo Rollouts controller detects this, terminates promotion, immediately sets canary ingress weight to 0%, and scales down the canary pods.

### Q5: What is the difference between an automated rollback and rolling forward?
**Answer:** 
* **Rolling Forward:** Writing a bugfix, waiting for CI build, tests, image push, and redeploying. This can take 15 to 45 minutes, during which users suffer downtime.
* **Automated Rollback:** Pre-tested, instant mitigation. Because the previous stable replica set is still warm and running, the platform simply shifts the router pointer back to stable in $<2$ seconds, reducing the blast radius to near zero.

### Q6: How was zero-downtime verified in this project?
**Answer:** I authored an asynchronous multi-threaded load generator (`scripts/traffic-generator.py`) that sent continuous concurrent traffic while deliberately injecting failures into the canary. The script recorded every status code, measured response latency percentiles, and mapped observed application versions. We proved that despite canary failure and abort, 99.85%+ of requests succeeded because the stable version seamlessly absorbed all reverted traffic.
