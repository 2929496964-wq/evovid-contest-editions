# Private AWS compute deployment (prepared, never deployed)

## Actual component
The same Docker image runs OpenCV 5 analysis and FFmpeg rendering on a private EC2 instance. It is not an S3-logo-only integration. All API/UI/job/audit bytes come from that worker. Losing the SSM tunnel produces a visible connection failure; there is no local fallback masquerading as AWS.

**Current evidence: local execution only. AWS account, resource creation, IAM, image upload, authentication-token creation and costs are not authorized or executed. The template and Docker image have not been validated by AWS or built in Docker here.**

## Explicit prerequisites
- User-approved AWS account/region, IAM role creation, cost limit, image upload and resource deployment.
- Existing private subnet/VPC with SSM/SSM messages, ECR API/DKR, S3 and Amazon Linux repository connectivity via appropriate VPC endpoints or existing NAT. This template deliberately does not create NAT gateways or internet exposure.
- Existing private ECR repository. `ImageUri` must be an immutable `@sha256:` digest matching `RepositoryArn`.
- A Linux x86_64 image build. The bundled FFmpeg from imageio-ffmpeg is used when system FFmpeg is absent. The tested host's system FFmpeg version differs; test the actual container before approval to deploy.

## After separate approval, operator commands
1. Build: `docker build --platform linux/amd64 -t evovid-vision:1.0.0 .`
2. Local container check using an operator-created token in a permission-restricted environment file: `docker run --rm -p 127.0.0.1:8712:8712 --env-file secure.env -v "$PWD/runtime:/app/runtime" evovid-vision:1.0.0`. Ensure the bind directory is writable by UID 10001. Do not commit secure.env or print its contents in evidence.
3. Operator signs into AWS using their normal short-lived authentication. Do not put keys in source, Docker build arguments or the image. Push the image to the approved ECR repository and retain its digest.
4. Review `private-ec2.yaml`, run AWS template validation and a change set. `EnableCompute=false` is the default and creates no resources. Enabling creates an IAM role/instance profile, private security group, encrypted EBS and EC2 instance. The UserData creates the local application access token. Get the necessary action-time approvals before enabling it.
5. Start the approved stack with `EnableCompute=true`. No public IPv4, inbound ports, SSH keys, internet load balancer or DNS name is created. EC2 enforces IMDSv2. The instance role has SSM access and pull access to one ECR repository.
6. Through an approved SSM shell, privately retrieve `/opt/vision/app.env` to the authorized operator; never include token in screenshots/log artifacts. Open a tunnel:
   `aws ssm start-session --target INSTANCE_ID --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["8712"],"localPortNumber":["8712"]}'`
7. Open http://127.0.0.1:8712 and enter the token. Run `VISION_ACCESS_TOKEN=... .venv/bin/python tools/e2e.py` from the operator workstation against the tunnel. Prefer setting the token without terminal history. It should not be pasted into chat or committed.
8. Save redacted stack events, region, image digest, instance ID, runtime version/buildinfo, HTTP audit report and output hash. Confirm that the actual remote process shows OpenCV 5.0.0 and that the output is created by that process. An environment label alone is not AWS proof.

## Costs and stop controls
- Default template disabled. Instance has CPU credits set to standard, a one-worker app, a 1.5-CPU/1.5-GB container cap, 150-MB uploads, 3-minute input limit, 30 sessions and 10 render attempts/session. These are caps, not a billing guarantee.
- Paid items can include EC2 runtime, EBS, ECR, NAT/endpoints and network transfer. No price is promised. Review current regional prices before approval.
- Stop EC2 when the evaluation window ends; a stopped instance's EBS and ECR storage may still incur charges. `--restart unless-stopped` means compute resumes if EC2 starts again.
- `DeletionPolicy: Retain`, `UpdateReplacePolicy: Retain`, and non-deleting encrypted root volume protect user media. Deleting the stack does **not** clean these retained resources or stop their costs. Inventory them explicitly, archive authorized data, then seek deletion approval before cleanup.
- AWS Budgets notifications are recommended for an approved budget, but not created here and are not hard spending caps.

## Security and operational limitations
Single user/single process; never enable multiple uvicorn workers. All authenticated sessions share one workstation. Do not expose publicly. The token is a shared administrator secret with a one-hour browser cookie; rotate it manually after stopping the service if disclosed. Keep uploads private. Containers run without root, capabilities or writable application files. Keep the host/runtime patched and use a reverse proxy/TLS plus stronger identity controls before any multi-user service. Cancellation/timeout cover FFmpeg; untrusted native decoders are contained by Docker memory/PID constraints but are not a formal sandbox guarantee.

Official references: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html · https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ec2-instance.html · https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_use-resources.html
