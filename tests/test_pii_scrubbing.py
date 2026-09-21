from customer_support_agent import CustomerSupportAgent


def make_agent(temp_db_path):
    return CustomerSupportAgent(db_path=temp_db_path)


def test_masks_email(temp_db_path):
    agent = make_agent(temp_db_path)
    result = agent._scrub_pii("Contact me at jane.doe@example.com please")
    assert "[EMAIL_MASKED]" in result
    assert "jane.doe@example.com" not in result


def test_masks_phone_number(temp_db_path):
    agent = make_agent(temp_db_path)
    result = agent._scrub_pii("Call me at +1 555-123-4567")
    assert "[PHONE_MASKED]" in result


def test_masks_ssn(temp_db_path):
    agent = make_agent(temp_db_path)
    result = agent._scrub_pii("My SSN is 123-45-6789 for verification")
    assert "[SSN_MASKED]" in result
    assert "123-45-6789" not in result


def test_masks_valid_credit_card_number(temp_db_path):
    agent = make_agent(temp_db_path)
    # 4111111111111111 is a standard Luhn-valid test Visa number
    result = agent._scrub_pii("My card number is 4111111111111111")
    assert "[CARD_MASKED]" in result
    assert "4111111111111111" not in result


def test_does_not_mask_luhn_invalid_sequences_as_a_card(temp_db_path):
    agent = make_agent(temp_db_path)
    # 1234567890123456 fails the Luhn check, so the card masker must not treat
    # it as a card number (unrelated pre-existing phone regex may still touch
    # a 10-digit substring within it — out of scope here, only card masking
    # is under test).
    result = agent._scrub_pii("Order reference 1234567890123456")
    assert "[CARD_MASKED]" not in result
