from core.java_json import apply_json_modification, java_to_json, json_to_java, merge_script_jsons, validate_script_json

JAVA = """package com.example.steps;

import io.cucumber.java.en.Given;
import io.restassured.RestAssured;

public class LoginSteps {

    private static final Logger logger = LogManager.getLogger(LoginSteps.class);
    private Response response;

    @Given("the API is available")
    public void theApiIsAvailable() {
        RestAssured.baseURI = "https://api.example.com";
        if (response == null) {
            logger.info("ready");
        }
    }

    @When("the user logs in as {string}")
    public void theUserLogsIn(String user) {
        response = RestAssured.given().body(user).post("/login");
    }
}"""


def test_java_to_json_extracts_structure():
    script = java_to_json(JAVA)
    assert script["package"] == "com.example.steps"
    assert script["className"] == "LoginSteps"
    assert sorted(script["imports"]) == ["io.cucumber.java.en.Given", "io.restassured.RestAssured"]
    assert [f["name"] for f in script["fields"]] == ["logger", "response"]
    login = script["methods"][1]
    assert login["name"] == "theUserLogsIn"
    assert login["parameters"] == [{"type": "String", "name": "user"}]
    assert login["annotations"] == [{"name": "When", "value": "the user logs in as {string}"}]
    assert validate_script_json(script) == (True, [])


def test_json_to_java_round_trip_is_stable():
    once = json_to_java(java_to_json(JAVA))
    assert json_to_java(java_to_json(once)) == once
    assert "    public void theApiIsAvailable() {" in once
    assert '            logger.info("ready");' in once


def test_merge_dedupes_imports_and_fields_and_keeps_all_methods():
    a = java_to_json(JAVA)
    b = java_to_json(JAVA.replace("theApiIsAvailable", "theApiIsUp").replace("theUserLogsIn", "theUserSignsIn"))
    merged = merge_script_jsons([a, b], "GeneratedTests")
    assert merged["className"] == "GeneratedTests"
    assert len(merged["imports"]) == 2
    assert [f["name"] for f in merged["fields"]] == ["logger", "response"]
    assert [m["id"] for m in merged["methods"]] == ["method_1", "method_2", "method_3", "method_4"]


def test_modifications_are_applied_without_mutating_input():
    script = java_to_json(JAVA)
    method_id = script["methods"][0]["id"]
    for mod in (
        {"action": "rename_class", "new_name": "AuthSteps"},
        {"action": "add_import", "import": "org.testng.Assert"},
        {"action": "rename_method", "method_id": method_id, "new_name": "apiIsUp"},
        {"action": "update_method_body", "method_id": method_id, "body": ["Assert.assertTrue(true);"]},
    ):
        updated = apply_json_modification(script if mod["action"] == "rename_class" else updated, mod)
    java = json_to_java(updated)
    assert "public class AuthSteps {" in java
    assert "import org.testng.Assert;" in java
    assert "public void apiIsUp() {\n        Assert.assertTrue(true);\n    }" in java
    assert script["className"] == "LoginSteps"
