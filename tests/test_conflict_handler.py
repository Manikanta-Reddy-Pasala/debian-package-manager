"""Tests for conflict handling and user interaction system."""

import os
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.conflict_handler import ConflictHandler, UserPrompt
from debian_metapackage_manager.models import Package, Conflict, DependencyPlan, PackageStatus, PackageType
from debian_metapackage_manager.classifier import PackageClassifier


def create_mock_classifier():
    """Create a mock package classifier."""
    mock_classifier = Mock(spec=PackageClassifier)
    mock_classifier.get_package_type.return_value = PackageType.SYSTEM
    mock_classifier.get_removal_risk_level.return_value = "LOW"
    mock_classifier.get_package_category_summary.return_value = "test packages"
    mock_classifier.is_custom_package.return_value = False
    mock_classifier.is_metapackage.return_value = False
    return mock_classifier


def test_conflict_handler_creation():
    """Test conflict handler can be created."""
    handler = ConflictHandler()
    assert handler is not None


def test_categorize_by_risk():
    """Test categorization of packages by risk level."""
    mock_classifier = create_mock_classifier()
    
    # Mock different risk levels
    def mock_risk_level(name):
        if name == "critical-pkg":
            return "HIGH"
        elif name == "medium-pkg":
            return "MEDIUM"
        else:
            return "LOW"
    
    mock_classifier.get_removal_risk_level.side_effect = mock_risk_level
    
    handler = ConflictHandler(mock_classifier)
    
    packages = [
        Package(name="critical-pkg", version="1.0.0"),
        Package(name="medium-pkg", version="1.0.0"),
        Package(name="safe-pkg", version="1.0.0")
    ]
    
    categories = handler._categorize_by_risk(packages)
    
    assert len(categories["HIGH"]) == 1
    assert len(categories["MEDIUM"]) == 1
    assert len(categories["LOW"]) == 1
    assert categories["HIGH"][0].name == "critical-pkg"
    assert categories["MEDIUM"][0].name == "medium-pkg"
    assert categories["LOW"][0].name == "safe-pkg"


@patch('builtins.input', return_value='y')
@patch('sys.stdout', new_callable=StringIO)
def test_prompt_for_removals_low_risk(mock_stdout, mock_input):
    """Test prompting for low-risk package removals."""
    mock_classifier = create_mock_classifier()
    mock_classifier.get_removal_risk_level.return_value = "LOW"
    
    handler = ConflictHandler(mock_classifier)
    
    packages = [Package(name="safe-pkg", version="1.0.0")]
    result = handler._prompt_for_removals(packages)
    
    assert result is True
    output = mock_stdout.getvalue()
    assert "LOW RISK REMOVALS" in output


@patch('builtins.input', return_value='YES')
@patch('sys.stdout', new_callable=StringIO)
def test_prompt_for_removals_high_risk(mock_stdout, mock_input):
    """Test prompting for high-risk package removals."""
    mock_classifier = create_mock_classifier()
    mock_classifier.get_removal_risk_level.return_value = "HIGH"
    
    handler = ConflictHandler(mock_classifier)
    
    packages = [Package(name="critical-pkg", version="1.0.0")]
    result = handler._prompt_for_removals(packages)
    
    assert result is True
    output = mock_stdout.getvalue()
    assert "HIGH RISK REMOVALS" in output
    assert "CRITICAL SYSTEM PACKAGE" in output


@patch('builtins.input', return_value='no')
@patch('sys.stdout', new_callable=StringIO)
def test_prompt_for_removals_declined(mock_stdout, mock_input):
    """Test declining package removals."""
    mock_classifier = create_mock_classifier()
    
    handler = ConflictHandler(mock_classifier)
    
    packages = [Package(name="test-pkg", version="1.0.0")]
    result = handler._prompt_for_removals(packages)
    
    assert result is False


def test_create_forced_resolution_plan():
    """Test creation of forced resolution plan."""
    handler = ConflictHandler()
    
    pkg1 = Package(name="package1", version="1.0.0")
    pkg2 = Package(name="package2", version="1.0.0")
    conflict = Conflict(package=pkg1, conflicting_package=pkg2, reason="Test conflict")
    
    plan = handler.create_forced_resolution_plan([conflict])
    
    assert len(plan.conflicts) == 1
    assert len(plan.to_remove) == 1
    assert plan.to_remove[0] == pkg2  # Conflicting package should be removed
    assert plan.requires_user_confirmation is True


@patch('sys.stdout', new_callable=StringIO)
def test_display_operation_result_success(mock_stdout):
    """Test displaying successful operation result."""
    handler = ConflictHandler()
    
    packages = [Package(name="test-pkg", version="1.0.0")]
    warnings = ["Test warning"]
    errors = []
    
    handler.display_operation_result(True, packages, warnings, errors)
    
    output = mock_stdout.getvalue()
    assert "OPERATION COMPLETED SUCCESSFULLY" in output
    assert "test-pkg" in output
    assert "Test warning" in output


@patch('sys.stdout', new_callable=StringIO)
def test_display_operation_result_failure(mock_stdout):
    """Test displaying failed operation result."""
    handler = ConflictHandler()
    
    packages = [Package(name="test-pkg", version="1.0.0")]
    warnings = []
    errors = ["Test error"]
    
    handler.display_operation_result(False, packages, warnings, errors)
    
    output = mock_stdout.getvalue()
    assert "OPERATION FAILED" in output
    assert "test-pkg" in output
    assert "Test error" in output


@patch('builtins.input', return_value='y')
@patch('sys.stdout', new_callable=StringIO)
def test_prompt_for_force_mode(mock_stdout, mock_input):
    """Test prompting for force mode."""
    handler = ConflictHandler()
    
    result = handler.prompt_for_force_mode("install", "test-package")
    
    assert result is True
    output = mock_stdout.getvalue()
    assert "INSTALL FAILED" in output
    assert "test-package" in output
    assert "Force mode options" in output


@patch('sys.stdout', new_callable=StringIO)
def test_display_package_info(mock_stdout):
    """Test displaying package information."""
    mock_classifier = create_mock_classifier()
    mock_classifier.get_package_type.return_value = PackageType.CUSTOM
    mock_classifier.is_custom_package.return_value = True
    mock_classifier.is_metapackage.return_value = False
    mock_classifier.get_removal_risk_level.return_value = "LOW"
    
    handler = ConflictHandler(mock_classifier)
    
    package = Package(name="test-pkg", version="1.0.0", status=PackageStatus.INSTALLED)
    dependencies = [Package(name="dep1", version="1.0.0")]
    
    handler.display_package_info(package, dependencies)
    
    output = mock_stdout.getvalue()
    assert "Package Information: test-pkg" in output
    assert "Version: 1.0.0" in output
    assert "Status: installed" in output
    assert "Type: custom" in output
    assert "Custom Package: Yes" in output
    assert "Metapackage: No" in output
    assert "Removal Risk: LOW" in output
    assert "Dependencies" in output
    assert "dep1" in output


@patch('builtins.input', return_value='y')
def test_user_prompt_confirm_operation_yes(mock_input):
    """Test user prompt confirmation - yes."""
    result = UserPrompt.confirm_operation("Test operation?")
    assert result is True


@patch('builtins.input', return_value='n')
def test_user_prompt_confirm_operation_no(mock_input):
    """Test user prompt confirmation - no."""
    result = UserPrompt.confirm_operation("Test operation?")
    assert result is False


@patch('builtins.input', return_value='')
def test_user_prompt_confirm_operation_default_true(mock_input):
    """Test user prompt confirmation - default true."""
    result = UserPrompt.confirm_operation("Test operation?", default=True)
    assert result is True


@patch('builtins.input', return_value='')
def test_user_prompt_confirm_operation_default_false(mock_input):
    """Test user prompt confirmation - default false."""
    result = UserPrompt.confirm_operation("Test operation?", default=False)
    assert result is False


@patch('builtins.input', return_value='2')
@patch('sys.stdout', new_callable=StringIO)
def test_user_prompt_select_from_options(mock_stdout, mock_input):
    """Test user prompt option selection."""
    options = ["Option 1", "Option 2", "Option 3"]
    result = UserPrompt.select_from_options("Choose an option:", options)
    
    assert result == "Option 2"
    output = mock_stdout.getvalue()
    assert "Choose an option:" in output
    assert "1. Option 1" in output
    assert "2. Option 2" in output
    assert "3. Option 3" in output


@patch('builtins.input', return_value='test input')
def test_user_prompt_get_text_input(mock_input):
    """Test user prompt text input."""
    result = UserPrompt.get_text_input("Enter text")
    assert result == "test input"


@patch('builtins.input', return_value='')
def test_user_prompt_get_text_input_optional(mock_input):
    """Test user prompt text input - optional."""
    result = UserPrompt.get_text_input("Enter text", required=False)
    assert result is None


@patch('builtins.input', side_effect=KeyboardInterrupt())
def test_user_prompt_keyboard_interrupt(mock_input):
    """Test user prompt handling keyboard interrupt."""
    result = UserPrompt.confirm_operation("Test operation?")
    assert result is False


@patch('builtins.input', return_value='y')
@patch('sys.stdout', new_callable=StringIO)
def test_handle_conflicts_no_conflicts(mock_stdout, mock_input):
    """Test handling conflicts when there are none."""
    handler = ConflictHandler()
    
    plan = DependencyPlan(
        to_install=[Package(name="test-pkg", version="1.0.0")],
        to_remove=[],
        to_upgrade=[],
        conflicts=[]
    )
    
    success, result_plan = handler.handle_conflicts(plan)
    
    assert success is True
    assert result_plan == plan


if __name__ == "__main__":
    test_conflict_handler_creation()
    test_categorize_by_risk()
    test_prompt_for_removals_low_risk()
    test_prompt_for_removals_high_risk()
    test_prompt_for_removals_declined()
    test_create_forced_resolution_plan()
    test_display_operation_result_success()
    test_display_operation_result_failure()
    test_prompt_for_force_mode()
    test_display_package_info()
    test_user_prompt_confirm_operation_yes()
    test_user_prompt_confirm_operation_no()
    test_user_prompt_confirm_operation_default_true()
    test_user_prompt_confirm_operation_default_false()
    test_user_prompt_select_from_options()
    test_user_prompt_get_text_input()
    test_user_prompt_get_text_input_optional()
    test_user_prompt_keyboard_interrupt()
    test_handle_conflicts_no_conflicts()
    print("All conflict handler tests passed!")