---
tags: [reference, area/aws]
---
# AWS sandbox
- Account: `486128667962`, region **eu-west-1 (Ireland) only**
- Console sign-in: `https://486128667962.signin.aws.amazon.com/console`
- Lead's IAM user: `patrick-admin`; CLI profile `hackathon` (`export AWS_PROFILE=hackathon`)
- Group `hackathon-admins` (AdministratorAccess): 8 members. Usernames are `first.last`; see IAM.
- Add a teammate: `bash ~/amalitech/aws-hackathon/create-team-users.sh first.last` (appends temp password to `team-credentials.txt`; delete after use)
- Bedrock: use `eu.*` profiles only → [[2026-10-13 EU-only Bedrock inference profiles|EU-only inference profiles]]

Related: [[Reference]], [[2026-10-13 Team are admins, workload roles least-privilege|IAM decision]]
