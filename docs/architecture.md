EduCloud Architecture

1. Overview

EduCloud uses Linux administration and AWS cloud services to
provide a secure trainer-student file-sharing portal.

The architecture includes Linux-based file management,
AWS storage, database services, application hosting,
backup, notification, and content delivery.

2. Linux Architecture

The Linux environment uses Amazon Linux 2.

The following users and groups are configured:

Users

- trainer1
- trainer2
- student1
- student2
- student3
- support1

Groups

- trainers
- students
- support

Directory Structure

| Directory | Trainers | Students | Support |

| /materials | Read/Write | Read Only | As configured |
| /assignments | Read Only | Read/Write | As configured |
| /logs | Read/Write | No Access | Read Only |

Access is controlled through Linux permissions and ACLs.

3. Linux Storage and Backup

- LVM is used to manage flexible storage.
- The training data volume is expanded from 5 GB to 10 GB.
- LUKS is used for encrypted storage.
- Cron jobs automate backup and archive operations.
- Bash scripts manage archive creation and S3 uploads.
- NFS provides shared directory access.

4. AWS Architecture

The AWS environment includes:

- VPC: EduCloudVPC
- VPC CIDR: 10.0.0.0/16
- Public subnet: 10.0.1.0/24
- Private subnet: 10.0.2.0/24
- Internet Gateway
- NAT Gateway
- EC2 instances
- Application Load Balancer
- Auto Scaling Group
- S3
- RDS MySQL
- Lambda
- SNS
- API Gateway
- CloudFront
- IAM
- CloudWatch

5. AWS Storage and Database

Amazon S3

The S3 bucket named educloud-materials is used for
storing project materials and backup files.

Configured storage features include:

- Versioning
- Lifecycle management
- Archival to Glacier after 90 days
- Cross-region replication to a backup bucket in us-west-2

Amazon RDS

The project uses an RDS MySQL database named educloud_db.

The database contains the following tables:

- students
- trainers
- uploads

6. Application and Notification Flow

- API Gateway provides the assignment submission endpoint.
- The API is connected to backend processing.
- Assignment metadata is stored in RDS.
- An S3 upload event triggers Lambda.
- Lambda sends notifications through SNS.

7. High Availability

- Application Load Balancer distributes incoming traffic.
- Auto Scaling Group manages EC2 instance capacity.
- The configured Auto Scaling range is a minimum of 2 and
  a maximum of 5 instances.
- CPU utilization above 60% for 5 minutes is used as a
  scaling condition.

