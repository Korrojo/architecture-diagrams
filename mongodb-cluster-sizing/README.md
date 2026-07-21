# MongoDB Cluster Sizing

Sanitized templates for collecting application workload information and producing an initial MongoDB Enterprise sizing assessment.

## Files

- [Application team questionnaire](application-team-questionnaire.md)
- [DBA and AWS sizing methodology](dba-sizing-methodology.md)
- [MongoDB AWS sizing calculator](mongodb-sizing-calculator.xlsx)
- [Sizing assessment template](sizing-assessment-template.md)

## Workflow

1. The application team completes the questionnaire using measured values where available.
2. The DBA reviews missing, estimated, and conflicting inputs.
3. Questionnaire values are transferred to the calculator.
4. The DBA enters measured IOPS, throughput, network, CPU, RTO/RPO tier, and platform requirements.
5. The calculator compares those requirements with AWS EC2 R7i/R8i and EBS gp3/io2 candidates.
6. The DBA prepares the sizing assessment, including assumptions and risks.
7. Representative performance testing validates the complete EC2 and EBS combination.
8. The assessment is revised after testing and again after production workload metrics become available.

## Scope

The questionnaire collects application and workload facts. It intentionally does not ask application teams to select CPU, RAM, EC2 instance types, EBS volume types, replica-set members, or shard counts. Those are DBA and architecture decisions.

AWS reference specifications in the workbook are dated and must be checked against current AWS documentation, regional availability, and organization-approved instance types before approval.

## Sanitization

Do not add organization names, application names, hostnames, IP addresses, account identifiers, credentials, internal URLs, or production data to this public repository.

## Disclaimer

The calculator provides an initial planning estimate. It is not a substitute for representative load testing, operational monitoring, or a production architecture review.
