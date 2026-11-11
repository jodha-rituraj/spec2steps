from core.java_merger import JavaFileMerger

FIRST = """package com.example.steps;
import io.restassured.RestAssured;
public class FirstSteps {
  private Response response;
  @Given("a")
  public void a() {
      if (true) {
          RestAssured.get("/a");
      }
  }
}"""

SECOND = """package com.example.steps;

import io.restassured.RestAssured;
import org.testng.Assert;

public class SecondSteps {
    private Response response;
    private String token = "x";

    @Then("b")
    public void b() {
        Assert.assertNotNull(token);
    }
}"""


def test_merge_combines_classes_into_one():
    merged = JavaFileMerger("GeneratedTests").merge([FIRST, SECOND])
    assert merged == """package com.example.steps;

import io.restassured.RestAssured;
import org.testng.Assert;

public class GeneratedTests {

    private Response response;
    private String token = "x";

    @Given("a")
    public void a() {
        if (true) {
            RestAssured.get("/a");
        }
    }

    @Then("b")
    public void b() {
        Assert.assertNotNull(token);
    }
}"""


def test_merge_uses_first_class_name_when_none_given():
    assert "public class FirstSteps {" in JavaFileMerger().merge([FIRST, SECOND])


def test_merge_points_class_literals_at_the_merged_class():
    first = FIRST.replace("private Response response;", "private Logger log = LogManager.getLogger(FirstSteps.class);")
    merged = JavaFileMerger("GeneratedTests").merge([first, SECOND])
    assert "LogManager.getLogger(GeneratedTests.class)" in merged
    assert "FirstSteps.class" not in merged
