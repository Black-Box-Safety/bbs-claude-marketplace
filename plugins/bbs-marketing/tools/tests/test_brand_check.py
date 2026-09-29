import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import brand_check as bc

CLAIMS_FIXTURE = """
# Claims Registry

Prose the parser must ignore.

## Registry

| id | approved wording | superseded wording | presence | scope | evidence | owner | verified | expires |
|---|---|---|---|---|---|---|---|---|
| dvbe-cert | CA DVBE Cert. 2009473 | CA SB/DVBE Cert. 2009473; California-registered DVBE | as-used | all | cert | Joey | 2026-08-13 | 2027-06-30 |
| sdvosb | SDVOSB | VA CVE Verified SDVOSB | as-used | all | cert | Joey | 2026-08-13 | 2026-09-15 |
| agency-disclaimer | Black Box Safety is an independent supplier. | | required | agency | policy | Griffin | 2026-08-13 | 2027-08-13 |

## Open

More prose.
"""


def test_parses_every_registry_row():
    claims = bc.parse_claims(CLAIMS_FIXTURE)
    assert [c.id for c in claims] == ["dvbe-cert", "sdvosb", "agency-disclaimer"]


def test_splits_superseded_wording_on_semicolons():
    claims = {c.id: c for c in bc.parse_claims(CLAIMS_FIXTURE)}
    assert claims["dvbe-cert"].superseded == [
        "CA SB/DVBE Cert. 2009473",
        "California-registered DVBE",
    ]


def test_empty_superseded_cell_yields_empty_list():
    claims = {c.id: c for c in bc.parse_claims(CLAIMS_FIXTURE)}
    assert claims["agency-disclaimer"].superseded == []


def test_parses_expiry_as_date():
    claims = {c.id: c for c in bc.parse_claims(CLAIMS_FIXTURE)}
    assert claims["sdvosb"].expires == dt.date(2026, 9, 15)


def test_missing_registry_heading_raises():
    try:
        bc.parse_claims("# Claims\n\nNo registry here.\n")
    except ValueError as e:
        assert "Registry" in str(e)
    else:
        raise AssertionError("expected ValueError")


TODAY = dt.date(2026, 8, 13)


def _claims():
    return bc.parse_claims(CLAIMS_FIXTURE)


def test_flags_superseded_sdvosb_wording():
    piece = "Black Box Safety is a VA CVE Verified SDVOSB serving California."
    findings = bc.audit(piece, _claims(), scopes=["all"], today=TODAY)
    assert [f.kind for f in findings] == ["superseded"]
    assert findings[0].claim_id == "sdvosb"
    assert "VA CVE Verified SDVOSB" in findings[0].detail


def test_flags_superseded_cert_rendering():
    piece = "CA SB/DVBE Cert. 2009473"
    findings = bc.audit(piece, _claims(), scopes=["all"], today=TODAY)
    assert [f.claim_id for f in findings] == ["dvbe-cert"]


def test_matches_superseded_wording_across_html_tags():
    piece = "<span>CA SB/DVBE</span> <b>Cert. 2009473</b>"
    findings = bc.audit(piece, _claims(), scopes=["all"], today=TODAY)
    assert [f.claim_id for f in findings] == ["dvbe-cert"]


def test_clean_piece_produces_no_findings():
    piece = "CA DVBE Cert. 2009473 - SDVOSB - El Cajon, CA"
    findings = bc.audit(piece, _claims(), scopes=["all"], today=TODAY)
    assert findings == []


def test_expired_claim_in_use_is_flagged():
    piece = "Black Box Safety is an SDVOSB."
    later = dt.date(2026, 10, 1)
    findings = bc.audit(piece, _claims(), scopes=["all"], today=later)
    assert [f.kind for f in findings] == ["expired"]
    assert findings[0].claim_id == "sdvosb"


def test_expired_claim_not_in_use_is_not_flagged():
    piece = "CA DVBE Cert. 2009473"
    later = dt.date(2026, 10, 1)
    findings = bc.audit(piece, _claims(), scopes=["all"], today=later)
    assert findings == []


def test_required_claim_missing_in_scope_is_flagged():
    piece = "Officer pricing on plate carriers."
    findings = bc.audit(piece, _claims(), scopes=["agency"], today=TODAY)
    assert [f.kind for f in findings] == ["missing"]
    assert findings[0].claim_id == "agency-disclaimer"


def test_required_claim_present_in_scope_passes():
    piece = "Officer pricing. Black Box Safety is an independent supplier."
    findings = bc.audit(piece, _claims(), scopes=["agency"], today=TODAY)
    assert findings == []


def test_required_claim_out_of_scope_is_not_required():
    piece = "Officer pricing on plate carriers."
    findings = bc.audit(piece, _claims(), scopes=["mro"], today=TODAY)
    assert findings == []


def test_scope_all_still_applies_to_a_narrow_scope():
    piece = "VA CVE Verified SDVOSB"
    findings = bc.audit(piece, _claims(), scopes=["mro"], today=TODAY)
    assert [f.claim_id for f in findings] == ["sdvosb"]


def test_superseded_matching_is_case_insensitive():
    piece = "BLACK BOX SAFETY IS A VA CVE VERIFIED SDVOSB"
    findings = bc.audit(piece, _claims(), scopes=["all"], today=TODAY)
    assert [f.claim_id for f in findings] == ["sdvosb"]
    assert "VA CVE Verified SDVOSB" in findings[0].detail


def test_required_claim_matches_case_insensitively():
    piece = "BLACK BOX SAFETY IS AN INDEPENDENT SUPPLIER."
    findings = bc.audit(piece, _claims(), scopes=["agency"], today=TODAY)
    assert findings == []


def test_normalize_decodes_html_entities():
    assert bc.normalize("Cert.&nbsp;2009473") == "Cert. 2009473"


def test_superseded_matching_survives_entities():
    piece = "<p>CA&nbsp;SB/DVBE Cert.&#160;2009473</p>"
    findings = bc.audit(piece, _claims(), scopes=["all"], today=TODAY)
    assert [f.claim_id for f in findings] == ["dvbe-cert"]


BLANK_REQUIRED_FIXTURE = """
## Registry

| id | approved wording | superseded wording | presence | scope | evidence | owner | verified | expires |
|---|---|---|---|---|---|---|---|---|
| broken |  |  | required | all | none | Joey | 2026-08-13 | 2027-06-30 |
"""


def test_required_row_with_blank_wording_fails_closed():
    claims = bc.parse_claims(BLANK_REQUIRED_FIXTURE)
    findings = bc.audit("anything at all", claims, scopes=["all"], today=TODAY)
    assert len(findings) == 1
    assert findings[0].claim_id == "broken"
    assert "malformed" in findings[0].detail.lower()


OVERLAP_FIXTURE = """
## Registry

| id | approved wording | superseded wording | presence | scope | evidence | owner | verified | expires |
|---|---|---|---|---|---|---|---|---|
| hq-city | El Cajon | headquartered in San Diego; headquartered in San Diego, CA | as-used | all | c | Joey | 2026-08-13 | 2027-06-30 |
"""


def test_overlapping_superseded_wordings_report_once():
    claims = bc.parse_claims(OVERLAP_FIXTURE)
    piece = "We are headquartered in San Diego, CA and proud of it."
    findings = bc.audit(piece, claims, scopes=["all"], today=TODAY)
    assert len(findings) == 1
    assert "headquartered in San Diego, CA" in findings[0].detail


def test_main_returns_zero_on_clean_piece(tmp_path):
    claims_file = tmp_path / "CLAIMS.md"
    claims_file.write_text(CLAIMS_FIXTURE)
    piece = tmp_path / "piece.html"
    piece.write_text("<p>CA DVBE Cert. 2009473</p>")
    code = bc.main([str(piece), "--claims", str(claims_file), "--scope", "mro"])
    assert code == 0


def test_main_returns_one_on_superseded_wording(tmp_path):
    claims_file = tmp_path / "CLAIMS.md"
    claims_file.write_text(CLAIMS_FIXTURE)
    piece = tmp_path / "piece.html"
    piece.write_text("<p>VA CVE Verified SDVOSB</p>")
    code = bc.main([str(piece), "--claims", str(claims_file), "--scope", "mro"])
    assert code == 1
