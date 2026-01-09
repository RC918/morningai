# Line 80 before fix:
# validation_results = perform_validation_step(step_name="step_3", data=data_payload, config=config_settings, additional_params={"timeout": 30, "retries": 5, "strict_mode": True})

# Line 80 after fix:
validation_results = perform_validation_step(
    step_name="step_3", data=data_payload, config=config_settings, 
    additional_params={"timeout": 30, "retries": 5, "strict_mode": True}
)