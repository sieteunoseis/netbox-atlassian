"""Data migration to seed additional document templates."""

from django.db import migrations

UPGRADE_MOP_CONTENT = """\
h1. Method of Procedure — {{ title|default:"(System Upgrade Title)" }}

h2. Change Summary

|| Field || Value || Field || Value ||
| Change Request # | {{ change_request|default:"(CHG-XXXXXX)" }} | MOP Author | {{ mop_author|default:"(Author)" }} |
| Change Window | {{ change_window|default:"(DDMONYYYY HHMM)" }} | Approved By | {{ approved_by|default:"(Approver Name)" }} |
| Expected Duration | {{ expected_duration|default:"(X hours)" }} | Impact Level | {{ impact_level|default:"(Low/Medium/High)" }} |
| Rollback Time | {{ rollback_time|default:"(X minutes)" }} | Rollback Deadline | {{ rollback_deadline|default:"(HHMM)" }} |

----

h2. 1. Definitions

|| Acronym || Definition ||
| (ACRONYM) | (Definition) |

----

h2. 2. Overview

{{ overview|default:"(Describe the upgrade scope, current version, target version, and business justification.)" }}

----

h2. 3. Personnel & Responsibilities

|| Role || Name || Contact || Location ||
{% for c in unique_contacts %}| {{ c.role.name|default:"(Role)" }} | {{ c.contact.name }} | {{ c.contact.phone|default:"N/A" }} | (On-site / Remote) |
{% endfor %}

----

h2. 4. Project Phases

|| Phase || Description || Owner || Target Date ||
| Phase 1 | (Pre-upgrade preparation) | (Owner) | (Date) |
| Phase 2 | (Upgrade execution) | (Owner) | (Date) |
| Phase 3 | (Post-upgrade validation) | (Owner) | (Date) |

----

h2. 5. Target Systems

|| Device || Site || Role || Current Version || Target Version || Primary IP ||
{% for device in devices %}| {{ device.name }} | {{ device.site.name }} | {{ device.role.name }} | (Current) | (Target) | {{ device.primary_ip4|default:"N/A" }} |
{% endfor %}

----

h2. 6. Prerequisites

* [ ] Maintenance window approved and scheduled
* [ ] Vendor TAC case opened (case #: )
* [ ] Upgrade files downloaded and verified (checksum match)
* [ ] Configuration backups taken for all target systems
{% for device in devices %}* [ ] Backup taken for {{ device.name }}
{% endfor %}* [ ] Rollback procedure documented and reviewed
* [ ] Stakeholders notified of upcoming change

----

h2. 7. Pre-Upgrade Tasks

* [ ] Verify all target systems are healthy and reachable
{% for device in devices %}* [ ] Verify {{ device.name }} — {{ device.primary_ip4|default:"N/A" }}
{% endfor %}* [ ] Upload upgrade files to target systems
* [ ] Confirm no active alarms or incidents
* [ ] Confirm change freeze exceptions (if applicable)

----

h2. 8. Communications

* [ ] Notify operations center of change start — *_5 minutes_*
* [ ] Notify application owners — *_5 minutes_*
* [ ] Notify monitoring team to suppress alerts — *_5 minutes_*
* [ ] Post status update to (channel/bridge) — *_2 minutes_*

----

h2. 9. Upgrade Steps

{% for device in devices %}
h3. {{ device.name }}

* [ ] Step 1 — (Pre-upgrade check) — *_X minutes_*
* [ ] Step 2 — (Apply upgrade) — *_X minutes_*
* [ ] Step 3 — (Verify upgrade version) — *_X minutes_*
* [ ] Step 4 — (Reboot/restart if required) — *_X minutes_*
* [ ] Step 5 — (Verify services restored) — *_X minutes_*
{% endfor %}

----

h2. 10. Post-Upgrade Validation

* [ ] Verify all systems on target version
* [ ] Run functional test suite
{% for device in devices %}* [ ] Validate {{ device.name }} functionality
{% endfor %}* [ ] Confirm monitoring shows healthy status
* [ ] Remove alert suppression
* [ ] Notify operations center of change completion

----

h2. 11. Rollback Plan

If the upgrade must be rolled back:

* [ ] Determine rollback trigger criteria
{% for device in devices %}* [ ] Rollback {{ device.name }} to previous version — *_X minutes_*
{% endfor %}* [ ] Verify rollback successful on all systems
* [ ] Notify stakeholders of rollback
* [ ] Open incident ticket for investigation

Estimated rollback time: {{ rollback_time|default:"(X minutes)" }}

----

h2. 12. Closeout

h3. Lessons Learned

* (Summary of unknowns encountered)
* (Changes made to the work plan during execution)
* (Process improvements identified)

h3. Disaster Recovery Plan Review

* [ ] Existing DR Plan Reviewed
* [ ] DR Plan — No Changes Needed
* [ ] DR Plan — Changes Confirmed and Updated

h3. System Diagram Review

* [ ] System Diagram(s) Reviewed
* [ ] Diagrams — No Changes Needed
* [ ] Diagrams — Changes Confirmed and Updated

h3. Additional Follow-Up Work

* (Follow-up item 1)
* (Follow-up item 2)

----

_Generated: {{ date }} by {{ generated_by }}_
"""

MAINTENANCE_RESET_CONTENT = """\
h1. Maintenance Reset — {{ title|default:"(System Name)" }}

|| Field || Value ||
| AOD | {{ aod|default:"(On-call name)" }} |
| Change Request # | {{ change_request|default:"(CHG-XXXXXX)" }} |
| Start | {{ start_time|default:"(HH:MM)" }} |
| Date | {{ date }} |

----

h2. Reset Schedule

|| Device || Reset Method || Monitor / Ack Method || IP || Time ||
{% for device in devices %}| {{ device.name }} | {{ reset_method|default:"(os/admin gui/cli)" }} | {{ monitor_method|default:"(icmp/admin gui)" }} | {{ device.primary_ip4|default:"N/A" }} | |
{% endfor %}| all remaining devices | (method) | (method) | | |

----

h2. Post-Reset Verification

{% for device in devices %}* [ ] {{ device.name }} — verified up and healthy
{% endfor %}

----

*All Clear:* (time)

----

_Generated: {{ date }} by {{ generated_by }}_
"""

FIRMWARE_UPGRADE_CONTENT = """\
h1. Firmware Upgrade — {{ title|default:"(Device Type / Platform)" }}

|| Field || Value || Field || Value ||
| Change Request # | {{ change_request|default:"(CHG-XXXXXX)" }} | Author | {{ mop_author|default:"(Author)" }} |
| Change Window | {{ change_window|default:"(DDMONYYYY HHMM)" }} | Approved By | {{ approved_by|default:"(Approver)" }} |
| Current Version | {{ current_version|default:"(X.Y.Z)" }} | Target Version | {{ target_version|default:"(X.Y.Z)" }} |
| Expected Duration | {{ expected_duration|default:"(X minutes per device)" }} | Rollback Time | {{ rollback_time|default:"(X minutes)" }} |

----

h2. 1. Overview

{{ overview|default:"(Describe the firmware upgrade scope and business justification.)" }}

h3. Release Notes Summary

* (Key fix or feature 1)
* (Key fix or feature 2)
* (Known issues in target version)

----

h2. 2. Target Devices

|| Device || Site || Role || Current FW || Primary IP ||
{% for device in devices %}| {{ device.name }} | {{ device.site.name }} | {{ device.role.name }} | (Current) | {{ device.primary_ip4|default:"N/A" }} |
{% endfor %}

----

h2. 3. Prerequisites

* [ ] Firmware image downloaded and checksum verified
* [ ] Release notes reviewed for known issues
* [ ] Vendor TAC case opened (if applicable): (case #)
* [ ] Lab testing completed (if applicable)
{% for device in devices %}* [ ] Configuration backup taken for {{ device.name }}
{% endfor %}

----

h2. 4. Upgrade Procedure

{% for device in devices %}
h3. {{ device.name }} ({{ device.primary_ip4|default:"N/A" }})

* [ ] Upload firmware image — *_X minutes_*
* [ ] Verify image integrity — *_2 minutes_*
* [ ] Set boot variable to new image — *_1 minute_*
* [ ] Reload device — *_X minutes_*
* [ ] Verify device comes back online — *_X minutes_*
* [ ] Confirm firmware version matches target — *_1 minute_*
* [ ] Run post-upgrade health checks — *_X minutes_*
{% endfor %}

----

h2. 5. Post-Upgrade Validation

{% for device in devices %}* [ ] {{ device.name }} — firmware version confirmed
* [ ] {{ device.name }} — services operational
{% endfor %}* [ ] No new alarms or errors in monitoring
* [ ] Stakeholders notified of completion

----

h2. 6. Rollback Plan

If the upgrade fails on any device:

* [ ] Boot to previous firmware image
* [ ] Verify device recovers on previous version
* [ ] Open incident ticket for investigation
* [ ] Notify stakeholders

----

_Generated: {{ date }} by {{ generated_by }}_
"""

DECOMMISSION_CONTENT = """\
h1. Decommission Plan — {{ title|default:"(System/Device Name)" }}

|| Field || Value || Field || Value ||
| Change Request # | {{ change_request|default:"(CHG-XXXXXX)" }} | Author | {{ mop_author|default:"(Author)" }} |
| Change Window | {{ change_window|default:"(DDMONYYYY HHMM)" }} | Approved By | {{ approved_by|default:"(Approver)" }} |
| Expected Duration | {{ expected_duration|default:"(X hours)" }} | Impact Level | {{ impact_level|default:"(Low/Medium/High)" }} |

----

h2. 1. Overview

{{ overview|default:"(Describe what is being decommissioned and why.)" }}

----

h2. 2. Personnel & Responsibilities

|| Role || Name || Contact ||
{% for c in unique_contacts %}| {{ c.role.name|default:"(Role)" }} | {{ c.contact.name }} | {{ c.contact.phone|default:"N/A" }} |
{% endfor %}

----

h2. 3. Systems to Decommission

|| Device || Site || Role || Model || Primary IP || Dependencies ||
{% for device in devices %}| {{ device.name }} | {{ device.site.name }} | {{ device.role.name }} | {% if device.device_type %}{{ device.device_type.manufacturer.name }} {{ device.device_type.model }}{% endif %} | {{ device.primary_ip4|default:"N/A" }} | (List dependencies) |
{% endfor %}

----

h2. 4. Pre-Decommission Checklist

* [ ] Confirm no active users or services depend on these systems
* [ ] Final configuration backup taken
{% for device in devices %}* [ ] Backup taken for {{ device.name }}
{% endfor %}* [ ] DNS records identified for removal
* [ ] Monitoring alerts identified for removal
* [ ] IP addresses identified for release
* [ ] License reclamation identified (if applicable)

----

h2. 5. Decommission Steps

{% for device in devices %}
h3. {{ device.name }}

* [ ] Disable monitoring alerts
* [ ] Gracefully shut down services
* [ ] Power off / disconnect
* [ ] Remove DNS records
* [ ] Release IP address ({{ device.primary_ip4|default:"N/A" }})
* [ ] Update inventory (NetBox status → Decommissioning)
{% endfor %}

----

h2. 6. Post-Decommission Tasks

* [ ] Verify no impact to dependent systems
* [ ] Remove from monitoring
* [ ] Remove from backup schedules
* [ ] Update network diagrams
* [ ] Update documentation and asset records
* [ ] Notify stakeholders of completion
* [ ] Schedule physical hardware removal (if applicable)

----

_Generated: {{ date }} by {{ generated_by }}_
"""


def seed_additional_templates(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    templates = [
        {
            "name": "Upgrade MOP (Multi-Phase)",
            "description": "Multi-phase system upgrade MOP with communications, closeout, and lessons learned sections.",
            "content": UPGRADE_MOP_CONTENT,
        },
        {
            "name": "Maintenance Reset",
            "description": "Quick maintenance reset/reboot schedule with device tracking table.",
            "content": MAINTENANCE_RESET_CONTENT,
        },
        {
            "name": "Firmware Upgrade",
            "description": "Per-device firmware upgrade procedure with version tracking and validation.",
            "content": FIRMWARE_UPGRADE_CONTENT,
        },
        {
            "name": "Decommission Plan",
            "description": "Device/system decommission plan with dependency checks and cleanup tasks.",
            "content": DECOMMISSION_CONTENT,
        },
    ]
    for t in templates:
        DocumentTemplate.objects.get_or_create(name=t["name"], defaults=t)


def remove_additional_templates(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    DocumentTemplate.objects.filter(
        name__in=[
            "Upgrade MOP (Multi-Phase)",
            "Maintenance Reset",
            "Firmware Upgrade",
            "Decommission Plan",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0009_remove_document_type"),
    ]

    operations = [
        migrations.RunPython(seed_additional_templates, reverse_code=remove_additional_templates),
    ]
