 EduCloud – Challenges and Learnings

1. Introduction

During the development of the EduCloud project, several technical challenges were encountered while configuring Linux services, managing storage, automating backups, and integrating AWS cloud services.

These challenges required troubleshooting, understanding system behaviour, identifying configuration errors, and verifying the results.

2. Technical Challenges Faced

2.1 Permission Conflicts Between Users and Groups

Challenge:

One of the major challenges was managing access to shared directories when multiple users belonged to different groups.

A user could have group membership but still fail to access a directory because of incorrect ownership, directory permissions, or ACL entries.

This made it difficult to identify whether the issue was caused by Linux ownership, group membership, or access permissions.

2.2 NFS Mount and Permission Issues

Challenge:

Configuring NFS access between the server and client systems involved multiple dependencies.

Even when a directory was exported from the server, the client could experience mounting or permission issues due to incorrect export configurations, firewall settings, or mismatched directory permissions.

Troubleshooting required checking both server-side and client-side configurations.

2.3 LVM Storage Expansion Problems

Challenge:

Expanding logical volumes was challenging because the physical volume, volume group, logical volume, and filesystem all had to be handled correctly.

Increasing the logical volume alone did not necessarily increase the available filesystem space.

Understanding the difference between allocated logical volume capacity and usable filesystem capacity was an important troubleshooting point.

2.4 LUKS Encrypted Volume Management

Challenge:

Working with encrypted storage required careful handling of the encryption device, mapping, formatting, and mounting process.

An incorrectly configured device mapping or mount operation could prevent access to the encrypted data.

It was also important to avoid losing access to sensitive information through incorrect encryption-key or passphrase management.

2.5 Cron Job Execution and Backup Scheduling

Challenge:

Automated backup jobs were difficult to troubleshoot because a script that worked when executed manually might behave differently when executed through Cron.

Environment variables, file permissions, working directories, and execution privileges could affect scheduled operations.

Verifying the correct execution time and ensuring that backup files were generated in the expected location required additional checks.

2.6 Shell Script and S3 Backup Integration

Challenge:

Integrating Linux backup scripts with Amazon S3 required handling local archive creation, file paths, AWS CLI configuration, and permissions.

A backup archive could be created successfully on the Linux system while its S3 upload failed because of incorrect bucket configuration, missing permissions, or AWS CLI issues.

This made it necessary to verify local backup creation and remote upload as separate operations.

2.7 AWS VPC Network Connectivity

Challenge:

Configuring communication between public and private resources was challenging because connectivity depended on multiple components working together.

An incorrect route table association, missing gateway route, or security group rule could prevent instances from reaching the required network destinations.

Identifying the exact source of connectivity problems required checking subnet routing, gateway configuration, and security group rules.

 2.8 Load Balancer and Auto Scaling Configuration

Challenge:

Configuring an Application Load Balancer with an Auto Scaling Group required understanding the relationship between EC2 instances, target groups, health checks, and scaling policies.

An instance could be running successfully but still fail the load balancer health check because the application service or health-check configuration was incorrect.

This highlighted the difference between EC2 instance status and application availability.

2.9 S3 Backup and Cross-Region Replication

Challenge:
Managing backup data across AWS regions involved understanding bucket versioning, replication permissions, destination bucket configuration, and lifecycle rules.

A replication configuration could appear complete while actual object replication was not working as expected.

Verifying the replication status and permissions was an important part of troubleshooting.

2.10 Integration of Multiple AWS Services

Challenge:

The EduCloud architecture involved several AWS services, including S3, Lambda, SNS, API Gateway, and RDS MySQL.

Understanding how these services communicate was challenging because each service has separate permissions, configurations, and execution requirements.

For example, an event-triggered Lambda function depends on the correct S3 event configuration and IAM permissions. Similarly, database operations depend on network connectivity and database access permissions.

3. Key Technical Learnings

Through these challenges, I gained practical understanding of:

- Troubleshooting Linux permission conflicts.
- Identifying NFS server and client configuration issues.
- Understanding logical volume and filesystem expansion.
- Managing encrypted storage safely.
- Debugging scheduled Cron jobs.
- Troubleshooting Bash scripts and AWS CLI operations.
- Diagnosing AWS VPC connectivity issues.
- Understanding load balancer health checks.
- Verifying S3 backup and replication operations.
- Understanding IAM permissions and AWS service integration.

4. Problem-Solving Approach

The following approach was useful while troubleshooting:

1. Identify the exact error or unexpected behaviour.
2. Check the relevant service or configuration.
3. Inspect logs and command outputs.
4. Verify permissions and dependencies.
5. Correct the identified configuration issue.
6. Repeat the operation.
7. Verify the final result.

