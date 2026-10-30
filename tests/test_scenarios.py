import pytest

from aethera.environmental_analysis import EnvironmentalAnalyzer


@pytest.mark.parametrize(
    "description, expected_category",
    [
        ("Someone is dumping garbage near the forest edge.", "illegal_dumping"),
        ("Plastic waste is piling up beside a local river.", "water_pollution"),
        ("A truck dumped old tires in a vacant lot.", "illegal_dumping"),
        ("The hill is full of trash after a weekend party.", "illegal_dumping"),
        ("Several trees were cut down in the neighbourhood park.", "deforestation"),
        ("The forest has been logged for a new road.", "deforestation"),
        ("Large trees were removed from a protected area.", "deforestation"),
        ("Forest clearing is happening near the stream.", "deforestation"),
        ("The pond is filled with plastic bottles and oily runoff.", "water_pollution"),
        ("The local river has cloudy water and foam.", "water_pollution"),
        ("A lake near town smells bad and has algae blooms.", "water_pollution"),
        ("A stream is contaminated with waste and chemicals.", "water_pollution"),
        ("Animals are disappearing from the wetland habitat.", "habitat_destruction"),
        ("Nests were destroyed after construction near the marsh.", "habitat_destruction"),
        ("Wildlife shelter areas have been damaged by bulldozing.", "habitat_destruction"),
        ("A nearby habitat is being fragmented by roads and fences.", "habitat_destruction"),
        ("Bird numbers are falling around the nature reserve.", "biodiversity_loss"),
        ("Species diversity in the forest is reducing quickly.", "biodiversity_loss"),
        ("The wetland has fewer frogs and reptiles than before.", "habitat_destruction"),
        ("Several local bird species are no longer seen in the area.", "biodiversity_loss"),
        ("Smoke is drifting from a burning landfill near homes.", "air_pollution"),
        ("Fumes from a factory are affecting air quality nearby.", "air_pollution"),
        ("Burning waste is creating heavy smoke in the street.", "air_pollution"),
        ("There is a strong smell and visible haze in the area.", "air_pollution"),
        ("I saw a strange patch of dead plants near the edge of the creek.", "general_environmental_concern"),
        ("There are signs of unusual environmental change but I am not certain what it is.", "general_environmental_concern"),
        ("The grass looks unhealthy and the soil seems disturbed.", "general_environmental_concern"),
        ("I am not sure what is happening, but the area looks damaged.", "general_environmental_concern"),
        ("Wildlife seems stressed and some animals are avoiding the area.", "habitat_destruction"),
        ("A canal is covered in floating rubbish and sewage.", "water_pollution"),
        ("There are dead fish floating in the river by the park.", "water_pollution"),
        ("Trees are being removed for a new housing project.", "deforestation"),
    ],
)
def test_scenario_classification(description, expected_category):
    analyzer = EnvironmentalAnalyzer()
    result = analyzer.parse_env_issue(description)
    assert result["category"] == expected_category
    assert "suggested_next_steps" in result
    assert "follow_up_questions" in result
