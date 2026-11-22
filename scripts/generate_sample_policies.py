"""Generate the fictional sample policy PDFs in data/policies/.

Run: python scripts/generate_sample_policies.py
All content is fictional and written for demonstration only.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "policies"
COMPANY = "Acme Technologies Pvt. Ltd."

# Each section: (heading, [paragraph | list-of-bullets, ...])
POLICIES: dict[str, dict] = {
    "Leave_Policy.pdf": {
        "title": "Leave Policy",
        "version": "Version 3.2, effective 1 April 2026",
        "sections": [
            ("1. Purpose and Scope", [
                "This policy defines the types of leave available to all full-time employees of "
                f"{COMPANY} and the rules for applying and approving them. It applies to every "
                "employee who has completed the joining formalities. Contract employees and interns "
                "follow the terms of their contract.",
            ]),
            ("2. Annual (Earned) Leave", [
                "Every employee is entitled to 18 days of annual leave per calendar year, accrued at "
                "1.5 days per month. Employees in their probation period of 3 months accrue leave but "
                "may use it only after confirmation.",
                [
                    "Up to 10 unused annual leave days can be carried forward to the next year. Days above 10 lapse on 31 December.",
                    "Up to 10 unused annual leave days can be encashed at year end at basic salary per day.",
                    "Leave of more than 3 consecutive days must be applied for at least 5 working days in advance through the HRMS portal.",
                ],
            ]),
            ("3. Sick Leave", [
                "Employees receive 10 days of paid sick leave per year. Sick leave does not carry forward.",
                [
                    "A medical certificate from a registered practitioner is required if sick leave exceeds 2 consecutive days.",
                    "The employee must inform their reporting manager before 10:00 AM on the first day of absence.",
                    "Sick leave taken immediately before or after a public holiday may require a medical certificate regardless of duration.",
                ],
            ]),
            ("4. Casual Leave", [
                "Employees receive 8 days of casual leave per year for short personal needs. Casual leave "
                "cannot be combined with annual leave and a maximum of 3 consecutive days may be taken at a time. "
                "Casual leave does not carry forward and cannot be encashed.",
            ]),
            ("5. Maternity, Paternity and Adoption Leave", [
                [
                    "Maternity leave: 26 weeks of paid leave for the first two children and 12 weeks for the third child onwards.",
                    "Paternity leave: 10 working days of paid leave, to be taken within 6 months of the child's birth.",
                    "Adoption leave: 12 weeks of paid leave for a primary adopting parent of a child below 3 months, and 6 weeks for other cases.",
                ],
            ]),
            ("6. Other Leave", [
                [
                    "Bereavement leave: 5 days of paid leave on the death of an immediate family member (spouse, parent, child, sibling).",
                    "Marriage leave: 5 days of paid leave, available once during employment.",
                    "Public holidays: 12 fixed holidays plus 2 floating holidays per year, published each January.",
                    "Loss of pay (unpaid) leave may be approved by the department head for up to 30 days when all paid leave is exhausted.",
                ],
            ]),
            ("7. Compensatory Off", [
                "An employee who works on a weekend or public holiday with prior manager approval earns a "
                "compensatory off. The compensatory off must be used within 60 days of the date worked, "
                "otherwise it lapses.",
            ]),
            ("8. Application and Approval", [
                "All leave must be applied for through the HRMS portal. The reporting manager approves or "
                "rejects the request within 2 working days. Unapproved absence of more than 3 consecutive days "
                "is treated as unauthorised absence and may lead to disciplinary action.",
            ]),
        ],
    },
    "Travel_Policy.pdf": {
        "title": "Business Travel Policy",
        "version": "Version 2.4, effective 1 April 2026",
        "sections": [
            ("1. Purpose", [
                f"This policy sets the rules for business travel undertaken on behalf of {COMPANY}. "
                "Employees are expected to travel in a cost-conscious manner and to obtain approval before booking.",
            ]),
            ("2. Approval and Booking", [
                [
                    "All business travel needs written approval from the reporting manager at least 7 days before departure. International travel also needs approval from the department head.",
                    "Flights, trains and hotels must be booked through the company travel desk (travel@acme-example.com). Personal bookings are reimbursed only if the travel desk cannot fulfil the request.",
                    "Book domestic flights at least 14 days in advance whenever possible to get lower fares.",
                ],
            ]),
            ("3. Air and Rail Travel", [
                [
                    "Domestic flights: economy class for all employees.",
                    "International flights: economy class by default. Business class is permitted only for Directors and above on flights longer than 6 hours.",
                    "Rail: AC 2-tier for employees up to Senior Manager level and AC 1st class for Directors and above.",
                ],
            ]),
            ("4. Hotel Accommodation", [
                "Hotel stays are reimbursed up to the following maximum per night, including taxes:",
                [
                    "Tier 1 cities (Mumbai, Delhi, Bengaluru, Chennai, Hyderabad, Kolkata, Pune): Rs. 6,000 per night.",
                    "Tier 2 cities: Rs. 4,000 per night.",
                    "Tier 3 cities and other locations: Rs. 3,000 per night.",
                    "International travel: up to USD 150 per night, or as approved by the department head.",
                ],
                "Stays above the limit need prior written approval from the department head.",
            ]),
            ("5. Meals and Daily Allowance (Per Diem)", [
                [
                    "Domestic travel: Rs. 1,200 per day for meals and incidentals, no receipts required.",
                    "International travel: USD 75 per day for meals and incidentals.",
                    "Alcohol is never reimbursable, even when part of a meal bill.",
                ],
            ]),
            ("6. Local Conveyance and Own Vehicle", [
                [
                    "Use app-based cabs or public transport for local travel. Receipts are required for any ride above Rs. 500.",
                    "Use of a personal car is reimbursed at Rs. 12 per km, and a personal two-wheeler at Rs. 5 per km, with a trip log.",
                    "Airport parking and tolls are reimbursed with receipts.",
                ],
            ]),
            ("7. Travel Advance and Settlement", [
                "Employees may request a travel advance of up to 80 percent of the estimated trip cost "
                "through the finance portal at least 3 working days before travel. The travel expense report "
                "must be submitted within 7 days of returning, and any unused advance must be refunded in the same period.",
            ]),
            ("8. Travel Insurance and Safety", [
                "All international travel is covered by the company group travel insurance. Employees must "
                "share their itinerary with HR and keep the emergency helpline number (1800-000-0000) with them at all times.",
            ]),
        ],
    },
    "Reimbursement_Policy.pdf": {
        "title": "Expense Reimbursement Policy",
        "version": "Version 4.0, effective 1 April 2026",
        "sections": [
            ("1. General Rules", [
                [
                    "Claims must be submitted through the finance portal within 30 days of the expense date. Claims submitted later than 30 days are rejected unless the CFO grants an exception.",
                    "Original receipts or valid tax invoices must be attached to every claim, except where the policy states that none is required.",
                    "Claims up to Rs. 5,000 need approval from the reporting manager. Claims above Rs. 5,000 need approval from both the reporting manager and the finance team.",
                    "Approved claims are paid within 10 working days into the salary bank account.",
                ],
            ]),
            ("2. Mobile and Internet", [
                "Employees are reimbursed up to Rs. 1,000 per month for mobile and home internet charges. "
                "A copy of the monthly bill must be uploaded with the claim.",
            ]),
            ("3. Work-From-Home Setup Allowance", [
                "Confirmed employees receive a one-time allowance of Rs. 15,000 for a work-from-home setup, "
                "such as a desk, chair or monitor. The allowance can be claimed once in the first 12 months "
                "after confirmation, and items purchased remain company property if the employee leaves within 12 months.",
            ]),
            ("4. Learning and Development", [
                "Each employee has a learning budget of Rs. 25,000 per financial year for courses, "
                "certifications, books and conferences related to their role. Courses above Rs. 10,000 need "
                "manager approval before purchase. Employees who leave within 6 months of completing a "
                "reimbursed certification must repay the amount.",
            ]),
            ("5. Client Meetings and Entertainment", [
                [
                    "Client meals and entertainment are reimbursed up to Rs. 3,000 per person, with prior manager approval.",
                    "The names and company of all attendees must be written on the claim.",
                    "Gifts to clients are limited to Rs. 2,000 in value and must be declared to the compliance team.",
                ],
            ]),
            ("6. Medical and Wellness", [
                "Employees can claim up to Rs. 10,000 per year for preventive health check-ups and wellness "
                "activities such as gym memberships. This is separate from the group medical insurance.",
            ]),
            ("7. Expenses That Are Not Reimbursable", [
                [
                    "Alcohol and tobacco.",
                    "Traffic fines, parking penalties and any legal penalties.",
                    "Personal expenses, family travel and personal entertainment.",
                    "Expenses without receipts, except those that the policy allows as no-receipt items.",
                    "Duplicate claims. Submitting a false claim is a serious violation and may lead to termination.",
                ],
            ]),
        ],
    },
    "Work_From_Home_Policy.pdf": {
        "title": "Hybrid Work and Work-From-Home Policy",
        "version": "Version 1.5, effective 1 April 2026",
        "sections": [
            ("1. Hybrid Model", [
                "Acme follows a hybrid model. Employees are expected to work from the office at least 3 days "
                "per week, on days agreed with their team. Tuesday and Wednesday are anchor days when all "
                "teams are expected in the office.",
            ]),
            ("2. Eligibility", [
                [
                    "Employees become eligible for hybrid work after completing their 3-month probation.",
                    "Employees on probation work from the office 5 days a week.",
                    "Fully remote work needs written approval from a Vice President and is reviewed every 6 months.",
                ],
            ]),
            ("3. Working Hours", [
                "Core working hours are 11:00 AM to 4:00 PM, Monday to Friday, when employees must be "
                "available on chat and for meetings. Employees can arrange the remaining hours flexibly "
                "with manager agreement, for a total of 8 hours per day.",
            ]),
            ("4. Working From Another City or Country", [
                [
                    "Working from a different city within India for up to 15 days per year is allowed with manager approval.",
                    "Working from another country is not permitted without approval from HR and the legal team, because of tax and data-protection rules.",
                ],
            ]),
            ("5. Equipment and Security", [
                [
                    "Employees must connect to the company VPN when accessing internal systems from home.",
                    "A stable internet connection of at least 25 Mbps is expected.",
                    "Company laptops must have disk encryption enabled and must not be used by family members.",
                    "Customer data must never be stored on personal devices or personal cloud accounts.",
                ],
            ]),
            ("6. Emergency Work From Home", [
                "In case of severe weather, transport strikes or public health emergencies, HR may declare "
                "emergency work from home for all employees, including those on probation. This does not use up leave balance.",
            ]),
        ],
    },
}


def _build_pdf(filename: str, spec: dict) -> Path:
    path = OUT_DIR / filename
    styles = getSampleStyleSheet()
    title = ParagraphStyle("PolicyTitle", parent=styles["Title"], fontSize=20, spaceAfter=4, alignment=TA_LEFT)
    meta = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=9, textColor="#555555", spaceAfter=14)
    heading = ParagraphStyle("H", parent=styles["Heading2"], fontSize=13, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("B", parent=styles["BodyText"], fontSize=10.5, leading=15, spaceAfter=6)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillGray(0.4)
        canvas.drawString(2 * cm, 1.2 * cm, f"{COMPANY} | {spec['title']} | Fictional sample document")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
        canvas.restoreState()

    story = [
        Paragraph(f"{COMPANY}", meta),
        Paragraph(spec["title"], title),
        Paragraph(spec["version"], meta),
    ]
    for head, blocks in spec["sections"]:
        story.append(Paragraph(head, heading))
        for block in blocks:
            if isinstance(block, list):
                story.append(
                    ListFlowable(
                        [ListItem(Paragraph(item, body), leftIndent=14) for item in block],
                        bulletType="bullet",
                        start="\u2022",
                        leftIndent=14,
                    )
                )
            else:
                story.append(Paragraph(block, body))
        story.append(Spacer(1, 2))

    SimpleDocTemplate(
        str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title=spec["title"], author=COMPANY,
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    return path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, spec in POLICIES.items():
        print("Created", _build_pdf(filename, spec))


if __name__ == "__main__":
    main()
