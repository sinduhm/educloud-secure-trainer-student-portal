 EduCloud Implementation Guide

1. Linux User and Group Management

Create the required Linux users:

- trainer1
- trainer2
- student1
- student2
- student3
- support1

Create the groups:

- trainers
- students
- support

Add users to their corresponding groups.

2. Directory Management

Create the directories:

- /materials
- /assignments
- /logs

Configure ownership and permissions according to the
project access requirements.

3. Access Control Lists

Use ACLs to provide additional permissions for users and groups.

Example commands:

sudo setfacl -m g:trainers:rwx /materials
sudo setfacl -m g:students:rx /materials
getfacl /materials