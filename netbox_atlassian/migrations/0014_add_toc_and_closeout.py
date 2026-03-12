"""Add {toc} to all templates and Closeout section to MOP templates that lack one."""

from django.db import migrations

CLOSEOUT_SECTION = """\

----

h2. Closeout

h3. Lessons Learned

* (Item 1)
* (Item 2)
* (Item 3)

h3. Disaster Recovery Plan Review

* [ ] Existing DR Plan Reviewed
* [ ] Existing DR Plan — No Changes Needed
* [ ] Existing DR Plan — Changes Confirmed
* DR Plan Link: (INSERT LINK HERE)
* Summary of changes: (INSERT SUMMARY HERE)

h3. System Diagram Review

* [ ] System Diagram(s) Reviewed
* [ ] Diagrams — No Changes Needed
* [ ] Diagrams — Changes Confirmed and Updated

h3. Additional Follow-Up Work

* (Follow-up item 1)
* (Follow-up item 2)"""

# Updated DR section for the Upgrade MOP that already has a closeout
OLD_DR = """\
* [ ] Existing DR Plan Reviewed
* [ ] DR Plan — No Changes Needed
* [ ] DR Plan — Changes Confirmed and Updated"""

NEW_DR = """\
* [ ] Existing DR Plan Reviewed
* [ ] Existing DR Plan — No Changes Needed
* [ ] Existing DR Plan — Changes Confirmed
* DR Plan Link: (INSERT LINK HERE)
* Summary of changes: (INSERT SUMMARY HERE)"""


def add_toc_and_closeout(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    for t in DocumentTemplate.objects.all():
        changed = False
        content = t.content

        # Add {toc} at the top if not present
        if "{toc}" not in content:
            content = "{toc}\n\n" + content.lstrip("\n")
            changed = True

        # Add closeout section to MOP templates that don't have one
        # (insert before the "Generated" footer line)
        if "Closeout" not in content and "Lessons Learned" not in content:
            # Only add to MOP-style templates (have "Rollback" or "Post-" sections)
            if "Rollback" in content or "Post-" in content:
                marker = "\n----\n\n_Generated:"
                if marker in content:
                    content = content.replace(marker, CLOSEOUT_SECTION + marker)
                    changed = True

        # Update DR section format in templates that already have closeout
        if OLD_DR in content:
            content = content.replace(OLD_DR, NEW_DR)
            changed = True

        if changed:
            t.content = content
            t.save()


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0013_remove_h1_from_templates"),
    ]

    operations = [
        migrations.RunPython(add_toc_and_closeout, reverse_code=migrations.RunPython.noop),
    ]
