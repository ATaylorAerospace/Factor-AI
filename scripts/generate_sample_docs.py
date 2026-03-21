#!/usr/bin/env python3
"""Generate sample legal documents for testing Factor.

Creates synthetic NDA, Lease, and Loan agreement text files.

WARNING: These are synthetic documents for testing only.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_docs"

SAMPLE_NDA = """NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is entered into as of [DATE],
by and between [PARTY A] ("Disclosing Party") and [PARTY B] ("Receiving Party").

1. CONFIDENTIAL INFORMATION
The Receiving Party agrees to hold in strict confidence all Confidential
Information disclosed by the Disclosing Party. "Confidential Information" means
any information that is proprietary, including trade secrets, business plans,
customer lists, and technical data.

2. NON-COMPETE
For a period of two (2) years following termination, the Receiving Party
shall not compete directly or indirectly with the Disclosing Party within
the United States.

3. INDEMNIFICATION
Each Party shall indemnify, defend, and hold harmless the other Party from
any losses, damages, or expenses arising from a breach of this Agreement.
Aggregate liability shall not exceed the fees paid under this Agreement.

4. LIMITATION OF LIABILITY
IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, INCIDENTAL,
SPECIAL, OR CONSEQUENTIAL DAMAGES. The aggregate liability of each Party
shall not exceed $500,000.

5. TERMINATION
Either Party may terminate this Agreement upon thirty (30) days' prior
written notice. A cure period of fifteen (15) days shall apply for
material breaches.

6. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the
laws of the State of New York, without regard to conflict of law principles.

7. ENTIRE AGREEMENT
This Agreement constitutes the entire agreement between the parties and
supersedes all prior negotiations, representations, and agreements.

8. SEVERABILITY
If any provision is held invalid or unenforceable, the remaining provisions
shall continue in full force and effect.

9. NOTICE
All notices must be in writing and delivered by certified mail to the
addresses specified herein.

IN WITNESS WHEREOF, the parties have executed this Agreement.
"""

SAMPLE_LEASE = """COMMERCIAL LEASE AGREEMENT

This Lease Agreement ("Lease") is entered into as of [DATE],
by and between [LANDLORD] ("Landlord") and [TENANT] ("Tenant").

1. PREMISES
Landlord leases to Tenant the premises located at [ADDRESS].

2. TERM
The lease term shall commence on [START DATE] and expire on [END DATE],
unless sooner terminated.

3. RENT
Tenant shall pay monthly rent of $[AMOUNT] due on the first day of each month.

4. INDEMNIFICATION
Tenant shall indemnify and hold harmless Landlord from any claims arising
from Tenant's use of the premises. This indemnification is unlimited and
at sole expense of the Tenant.

5. TERMINATION
Either party may terminate upon ninety (90) days' written notice. In the
event of material breach, immediate termination is permitted.

6. FORCE MAJEURE
Neither party shall be liable for failure to perform due to force majeure
events including natural disasters, pandemics, and acts of government.

7. REPRESENTATIONS AND WARRANTIES
Landlord represents and warrants that the premises comply with all
applicable building codes and safety regulations.

8. GOVERNING LAW
This Lease shall be governed by the laws of the State of California.

9. ENTIRE AGREEMENT
This Lease constitutes the entire agreement between the parties.

10. NOTICE
All notices shall be in writing and sent to the addresses listed herein.
"""

SAMPLE_LOAN = """LOAN AGREEMENT

This Loan Agreement ("Agreement") is entered into as of [DATE],
by and between [LENDER] ("Lender") and [BORROWER] ("Borrower").

1. PRINCIPAL AMOUNT
Lender agrees to lend Borrower the principal amount of $[AMOUNT].

2. INTEREST RATE
The loan shall bear interest at [RATE]% per annum.

3. REPRESENTATIONS AND WARRANTIES
Borrower represents and warrants that all financial statements provided
are true and accurate and that Borrower has the authority to enter into
this Agreement.

4. INDEMNIFICATION
Borrower shall indemnify Lender against all losses arising from any
breach of representations or covenants. No liability cap applies.

5. CHANGE OF CONTROL
In the event of a change of control of Borrower, including any merger
or acquisition, Lender may declare all amounts immediately due and payable.
Consent of Lender is required for any assignment.

6. TERMINATION
This Agreement shall terminate upon full repayment of the loan.
Lender may accelerate repayment upon default with no cure period.

7. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.

8. WAIVER
No waiver of any provision shall constitute a waiver of any other provision.
All amendments must be in writing.

9. SEVERABILITY
If any provision is held invalid, the remaining provisions remain in effect.

10. NOTICE
All notices shall be in writing and delivered to the addresses specified.
"""


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    docs = {
        "sample_nda.txt": SAMPLE_NDA,
        "sample_lease.txt": SAMPLE_LEASE,
        "sample_loan.txt": SAMPLE_LOAN,
    }

    for filename, content in docs.items():
        path = OUTPUT_DIR / filename
        path.write_text(content)
        print(f"Generated: {path}")

    print(f"\nGenerated {len(docs)} sample documents in {OUTPUT_DIR}")
    print("WARNING: These are synthetic documents for testing only.")


if __name__ == "__main__":
    main()
