"""Data migration to seed sample document templates."""

from django.db import migrations

MOP_CONTENT = """\
h1. Method of Procedure — {{ title|default:"(Change Title)" }}
{{ subtitle|default:"" }}

h2. Change Summary

|| Field || Value || Field || Value ||
| Change Request # | {{ change_request|default:"(ITSUP-XXXXXX)" }} | MOP Author | {{ mop_author|default:"(Author)" }} |
| Change Window | {{ change_window|default:"(DDMONYYYY HHMM)" }} | Approved By | {{ approved_by|default:"(Approver Name)" }} |
| Expected Duration | {{ expected_duration|default:"(X minutes)" }} | Impact Level | {{ impact_level|default:"(Low/Medium/High)" }} |
| Rollback Time | {{ rollback_time|default:"(X minutes)" }} | Rollback Deadline | {{ rollback_deadline|default:"(HHMM)" }} |

----

h2. 1. Personnel & Responsibilities

|| Role || Name || Contact || Responsibility ||
{% for c in unique_contacts %}| {{ c.role.name|default:"(Role)" }} | {{ c.contact.name }} | {{ c.contact.phone|default:"N/A" }} | (Responsibility) |
{% endfor %}

----

h2. 2. Overview

{{ overview|default:"(Describe the purpose and scope of this change.)" }}

h3. Key Considerations

* (Key consideration 1)
* (Key consideration 2)
* (Key consideration 3)

----

h2. 3. Affected Devices

{% for device in devices %}
h3. {{ device.name }}

|| Field || Value ||
| Site | {{ device.site.name }} |
| Role | {{ device.role.name }} |
{% if device.device_type %}| Manufacturer | {{ device.device_type.manufacturer.name }} |
| Model | {{ device.device_type.model }} |
{% endif %}{% if device.cluster %}| Cluster | {{ device.cluster.name }} |
{% endif %}{% if device.serial %}| Serial Number | {{ device.serial }} |
{% endif %}{% if device.asset_tag %}| Asset Tag | {{ device.asset_tag }} |
{% endif %}| Primary IP | {{ device.primary_ip4|default:"N/A" }} |
{% if device.rack %}| Rack | {{ device.rack }} |
{% endif %}

h4. Interfaces

|| Interface || Description || IP Address(es) ||
{% for iface in device.interfaces.all %}| {{ iface.name }} | {{ iface.description|default:"" }} | {% for ip in iface.ip_addresses.all %}{{ ip.address }} {% endfor %} |
{% endfor %}
{% endfor %}

----

h2. 4. Pre-Change Verification

* [ ] Confirm change window is approved and stakeholders notified
* [ ] Verify current connectivity / baseline state
* [ ] Confirm rollback procedure is understood and ready
{% for device in devices %}* [ ] Verify {{ device.name }} is reachable ({{ device.primary_ip4|default:"N/A" }})
{% endfor %}

----

h2. 5. Change Steps

* [ ] Step 1 — (Description)
* [ ] Step 2 — (Description)
* [ ] Step 3 — (Description)

----

h2. 6. Post-Change Verification

* [ ] Verify expected functionality restored / working
* [ ] Confirm no alerts or errors in monitoring
{% for device in devices %}* [ ] Verify {{ device.name }} operating normally
{% endfor %}* [ ] Update change ticket and notify stakeholders

----

h2. 7. Rollback Plan

If the change must be rolled back:

* [ ] Rollback Step 1 — (Description)
* [ ] Rollback Step 2 — (Description)
* [ ] Notify stakeholders of rollback

----

_Generated: {{ date }} by {{ generated_by }}_
"""

SOW_CONTENT = """\
h1. Statement of Work — {{ title|default:"(Project Title)" }}

|| Field || Value ||
| Project # | {{ project_number|default:"(Project Number)" }} |
| Prepared By | {{ prepared_by|default:"(Author)" }} |
| Date | {{ date }} |
| Version | {{ version|default:"1.0" }} |
| Approved By | {{ approved_by|default:"(Approver)" }} |

----

h2. 1. Project Overview

{{ overview|default:"(Describe the scope and purpose of the work.)" }}

----

h2. 2. Scope of Work

h3. In Scope

* (Item 1)
* (Item 2)

h3. Out of Scope

* (Item 1)
* (Item 2)

----

h2. 3. Affected Devices

{% for device in devices %}
h3. {{ device.name }}

|| Field || Value ||
| Site | {{ device.site.name }} |
| Role | {{ device.role.name }} |
{% if device.device_type %}| Model | {{ device.device_type.manufacturer.name }} {{ device.device_type.model }} |
{% endif %}{% if device.serial %}| Serial Number | {{ device.serial }} |
{% endif %}| Primary IP | {{ device.primary_ip4|default:"N/A" }} |
{% endfor %}

----

h2. 4. Deliverables

* (Deliverable 1)
* (Deliverable 2)

----

h2. 5. Timeline

|| Milestone || Target Date ||
| (Milestone 1) | (Date) |
| (Milestone 2) | (Date) |
| Project Complete | (Date) |

----

h2. 6. Assumptions & Dependencies

* (Assumption 1)
* (Assumption 2)

----

h2. 7. Acceptance Criteria

* (Criterion 1)
* (Criterion 2)

----

_Generated: {{ date }} by {{ generated_by }}_
"""

CAB_CONTENT = """\
h1. Change Advisory Board Request

|| Field || Value || Field || Value ||
| Change Request # | {{ change_request|default:"(ITSUP-XXXXXX)" }} | Submitted By | {{ submitted_by|default:"(Name)" }} |
| Change Type | {{ change_type|default:"(Normal/Standard/Emergency)" }} | Priority | {{ priority|default:"(Low/Medium/High)" }} |
| Requested Window | {{ change_window|default:"(DDMONYYYY HHMM)" }} | Duration | {{ expected_duration|default:"(X minutes)" }} |
| Impact | {{ impact_level|default:"(Low/Medium/High)" }} | Risk | {{ risk_level|default:"(Low/Medium/High)" }} |

----

h2. 1. Description of Change

{{ description|default:"(Describe what is being changed and why.)" }}

----

h2. 2. Business Justification

{{ justification|default:"(Explain the business need driving this change.)" }}

----

h2. 3. Affected Systems

|| Device || Site || Role || Model || Primary IP ||
{% for device in devices %}| {{ device.name }} | {{ device.site.name }} | {{ device.role.name }} | {% if device.device_type %}{{ device.device_type.manufacturer.name }} {{ device.device_type.model }}{% endif %} | {{ device.primary_ip4|default:"N/A" }} |
{% endfor %}

----

h2. 4. Risk Assessment

|| Risk || Likelihood || Impact || Mitigation ||
| Service disruption | (Low/Med/High) | (Low/Med/High) | (Mitigation) |
| Rollback required | (Low/Med/High) | (Low/Med/High) | (Mitigation) |

----

h2. 5. Implementation Plan (Summary)

* [ ] Step 1 — (Description)
* [ ] Step 2 — (Description)
* [ ] Step 3 — (Description)

----

h2. 6. Rollback Plan

* [ ] Rollback Step 1 — (Description)
* [ ] Rollback Step 2 — (Description)
* [ ] Estimated rollback time: {{ rollback_time|default:"(X minutes)" }}

----

h2. 7. Communications Plan

* Notify: (Stakeholders)
* Method: (Email / Teams / Phone)
* Timing: (Before / During / After change)

----

h2. 8. CAB Decision

|| Decision || Date || Approved By || Notes ||
| (Approved / Rejected / Deferred) | (Date) | (Name) | (Notes) |

----

_Generated: {{ date }} by {{ generated_by }}_
"""


def seed_templates(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    templates = [
        {
            "name": "Standard Network Change MOP",
            "document_type": "mop",
            "description": "Standard method of procedure for network device changes. Loops through selected devices.",
            "content": MOP_CONTENT,
        },
        {
            "name": "Standard Statement of Work",
            "document_type": "sow",
            "description": "Statement of work template for project scoping and delivery.",
            "content": SOW_CONTENT,
        },
        {
            "name": "Standard CAB Request",
            "document_type": "cab",
            "description": "Change Advisory Board request template with risk assessment.",
            "content": CAB_CONTENT,
        },
    ]
    for t in templates:
        DocumentTemplate.objects.get_or_create(name=t["name"], defaults=t)


def remove_sample_templates(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    DocumentTemplate.objects.filter(
        name__in=[
            "Standard Network Change MOP",
            "Standard Statement of Work",
            "Standard CAB Request",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0003_documenttemplate"),
    ]

    operations = [
        migrations.RunPython(seed_templates, reverse_code=remove_sample_templates),
    ]
