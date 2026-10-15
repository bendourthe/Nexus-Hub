# Empty States, Errors, and Confirmations

Read this when writing first-use empties, search-zero, load failures, or destroy/charge confirms.

## Empty vs zero vs error

Do not reuse one string. The user's next click is different in each case.

**First-use empty** (the feature has never had a row):

- Heading: what this list will hold ("No invoices yet")
- Body: one sentence on why they would create one
- Action: the create verb ("Create invoice")

**Zero result** (they searched or filtered):

- Heading: "No invoices match"
- Body: include the query or filter names
- Action: "Clear filters" and/or "Create invoice"

**Load error**:

- Heading: "Couldn't load invoices"
- Body: a recoverable reason if you have one ("Check your connection")
- Action: "Try again"

Loading copy is present tense and specific ("Loading invoices..."). If the wait is under about one second, visible text is optional but the accessible name on the busy indicator is not (`accessibility-engineering`).

## Destructive confirmation

Structure:

1. Title: verb + object ("Delete invoice INV-1042")
2. Body: consequence in one sentence ("This cannot be undone.")
3. Buttons: trailing destructive button uses the same verb + object; the dismiss control is "Cancel", not "No"

If the object name is user-supplied, show it. If it is missing, say "this invoice" rather than an empty pair of quotes.

Do not require typing the name unless the product already does that for this class of action; do not invent a type-to-confirm pattern in a codebase that does not have one.

## Charge and send confirms

Same structure as destructive: name the volume or amount ("Send this invoice to 12 recipients", "Charge $40.00 to the card ending 4242"). The confirm button is "Send invoice" / "Charge $40.00", not "Confirm".

## Tone

- First-use empty may be slightly warmer than the rest of the app if the product already is.
- Zero-result is neutral and practical.
- Errors and destructive confirms are plain and calm. No exclamation marks. No "Oops". No emoji in these strings unless the product's shipped UI already uses emoji on the same class of screen (do not be the first).
