"""Main CLI Entry Point."""
import argparse
import sys
import os
import json
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from cli.config import Config
from cli.errors import CLIError, ConfigurationError, GraphStoreError
from cli.utils import (
    ProgressIndicator, format_output, print_success, print_error, 
    print_warning, print_info
)
from graph.graph_store import GraphStore
from assessment.profiler import Profiler
from assessment.analyzer import Analyzer
from assessment.wave_planner import WavePlanner
from assessment.report_generator import ReportGenerator
from assessment.tco_calculator import TCOCalculator
from reconciliation.recon_engine import ReconciliationEngine
from utils.logger import get_logger

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="informatica-modernize",
        description="Informatica Modernization Accelerator CLI"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--api-url",
        type=str,
        help="API URL for HTTP mode (default: direct mode)"
    )
    
    parser.add_argument(
        "--workspace-dir",
        type=str,
        default="workspace",
        help="Workspace directory for operations"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Assessment commands
    assess_parser = subparsers.add_parser("assess", help="Assessment commands")
    assess_subparsers = assess_parser.add_subparsers(dest="assess_command", help="Assessment subcommand")
    
    # assess profile
    assess_subparsers.add_parser("profile", help="Profile repository")
    
    # assess analyze
    assess_subparsers.add_parser("analyze", help="Analyze components and identify blockers")
    
    # assess waves
    waves_parser = assess_subparsers.add_parser("waves", help="Generate migration wave plan")
    waves_parser.add_argument("--max-wave-size", type=int, default=10, help="Maximum components per wave")
    
    # assess report
    report_parser = assess_subparsers.add_parser("report", help="Generate assessment report")
    report_parser.add_argument("--format", choices=["json", "html", "summary"], default="json", help="Report format")
    report_parser.add_argument("--output", type=str, help="Output file path")
    
    # assess tco
    tco_parser = assess_subparsers.add_parser("tco", help="Calculate TCO and ROI")
    tco_parser.add_argument("--informatica-cost", type=float, help="Annual Informatica cost")
    tco_parser.add_argument("--migration-cost", type=float, help="One-time migration cost for ROI")
    tco_parser.add_argument("--runtime-hours", type=float, help="Current runtime hours per day")
    tco_parser.add_argument("--output", type=str, help="Output file path")
    
    # Reconciliation commands
    recon_parser = subparsers.add_parser("reconcile", help="Reconciliation commands")
    recon_subparsers = recon_parser.add_subparsers(dest="recon_command", help="Reconciliation subcommand")
    
    # reconcile mapping
    recon_mapping_parser = recon_subparsers.add_parser("mapping", help="Reconcile a mapping")
    recon_mapping_parser.add_argument("--mapping-name", required=True, help="Mapping name")
    recon_mapping_parser.add_argument("--source-connection", type=str, help="Source connection JSON or file path")
    recon_mapping_parser.add_argument("--target-connection", type=str, help="Target connection JSON or file path")
    recon_mapping_parser.add_argument("--method", choices=["count", "hash", "threshold", "sampling"], default="count", help="Comparison method")
    recon_mapping_parser.add_argument("--output", type=str, help="Output file path")
    
    # reconcile workflow
    recon_workflow_parser = recon_subparsers.add_parser("workflow", help="Reconcile a workflow")
    recon_workflow_parser.add_argument("--workflow-name", required=True, help="Workflow name")
    recon_workflow_parser.add_argument("--source-connection", type=str, help="Source connection JSON or file path")
    recon_workflow_parser.add_argument("--target-connection", type=str, help="Target connection JSON or file path")
    recon_workflow_parser.add_argument("--method", choices=["count", "hash", "threshold", "sampling"], default="count", help="Comparison method")
    recon_workflow_parser.add_argument("--output", type=str, help="Output file path")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Configuration commands")
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="Config subcommand")
    config_subparsers.add_parser("show", help="Show current configuration")
    config_subparsers.add_parser("validate", help="Validate configuration")
    
    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload Informatica XML files")
    upload_parser.add_argument("path", help="File or directory path to upload")
    upload_parser.add_argument("--recursive", action="store_true", help="Recursively upload files from directory")
    upload_parser.add_argument("--session-id", type=str, help="Session ID to group uploads")
    
    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse Informatica XML files")
    parse_parser.add_argument("target", nargs="?", help="File ID, file path, directory, or use --session-id")
    parse_parser.add_argument("--type", choices=["mapping", "workflow", "session", "worklet", "mapplet", "all"],
                             help="File type (auto-detected if not specified)")
    parse_parser.add_argument("--session-id", type=str, help="Session ID from upload")
    parse_parser.add_argument("--enhance", action="store_true", help="Enhance with AI")
    parse_parser.add_argument("--recursive", action="store_true", help="Recursively parse directory")
    parse_parser.add_argument("--output", type=str, help="Output directory")
    
    # Enhance command
    enhance_parser = subparsers.add_parser("enhance", help="Enhance canonical model with AI")
    enhance_parser.add_argument("mapping_name", help="Mapping name or ID")
    enhance_parser.add_argument("--output", type=str, help="Output directory")
    
    # Generate code command
    generate_parser = subparsers.add_parser("generate-code", help="Generate code from canonical model")
    generate_parser.add_argument("mapping_name", help="Mapping name or ID")
    generate_parser.add_argument("--type", choices=["pyspark", "dlt", "sql", "orchestration", "all"],
                                default="pyspark", help="Code type to generate")
    generate_parser.add_argument("--output", type=str, help="Output directory")
    generate_parser.add_argument("--review", action="store_true", help="Review generated code")
    
    # Review command
    review_parser = subparsers.add_parser("review", help="Review generated code with AI")
    review_parser.add_argument("path", help="File path or directory")
    review_parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    review_parser.add_argument("--output", type=str, help="Output directory")
    
    # Fix command
    fix_parser = subparsers.add_parser("fix", help="Fix code issues")
    fix_parser.add_argument("path", help="File path or directory")
    fix_parser.add_argument("--output", type=str, help="Output directory")
    
    return parser


def cmd_assess_profile(config: Config, args: argparse.Namespace):
    """Execute assess profile command."""
    try:
        print_info("Profiling repository...")
        
        graph_store = GraphStore(
            uri=config.get("neo4j.uri"),
            user=config.get("neo4j.user"),
            password=config.get("neo4j.password")
        )
        
        profiler = Profiler(graph_store)
        profile = profiler.profile_repository()
        
        print_success("Repository profiling complete")
        print(format_output(profile, format_type="json"))
        
    except Exception as e:
        print_error(f"Failed to profile repository: {str(e)}")
        sys.exit(1)


def cmd_assess_analyze(config: Config, args: argparse.Namespace):
    """Execute assess analyze command."""
    try:
        print_info("Analyzing repository...")
        
        graph_store = GraphStore(
            uri=config.get("neo4j.uri"),
            user=config.get("neo4j.user"),
            password=config.get("neo4j.password")
        )
        
        analyzer = Analyzer(graph_store)
        patterns = analyzer.identify_patterns()
        blockers = analyzer.identify_blockers()
        effort = analyzer.estimate_migration_effort()
        
        analysis = {
            "patterns": patterns,
            "blockers": blockers,
            "effort_estimates": effort
        }
        
        print_success("Analysis complete")
        print(format_output(analysis, format_type="json"))
        
    except Exception as e:
        print_error(f"Failed to analyze repository: {str(e)}")
        sys.exit(1)


def cmd_assess_waves(config: Config, args: argparse.Namespace):
    """Execute assess waves command."""
    try:
        print_info(f"Generating migration waves (max size: {args.max_wave_size})...")
        
        graph_store = GraphStore(
            uri=config.get("neo4j.uri"),
            user=config.get("neo4j.user"),
            password=config.get("neo4j.password")
        )
        
        wave_planner = WavePlanner(graph_store)
        waves = wave_planner.plan_migration_waves(max_wave_size=args.max_wave_size)
        
        report_generator = ReportGenerator(graph_store)
        wave_plan = report_generator.generate_wave_plan(max_wave_size=args.max_wave_size)
        
        print_success(f"Generated {len(waves)} migration waves")
        print(format_output(wave_plan, format_type="json"))
        
    except Exception as e:
        print_error(f"Failed to generate migration waves: {str(e)}")
        sys.exit(1)


def cmd_assess_report(config: Config, args: argparse.Namespace):
    """Execute assess report command."""
    try:
        print_info("Generating assessment report...")
        
        graph_store = GraphStore(
            uri=config.get("neo4j.uri"),
            user=config.get("neo4j.user"),
            password=config.get("neo4j.password")
        )
        
        report_generator = ReportGenerator(graph_store)
        
        if args.format == "summary":
            report = report_generator.generate_summary_report()
        elif args.format == "html":
            report = report_generator.generate_detailed_report()
        else:
            report = report_generator.generate_detailed_report()
        
        if args.output:
            output_path = Path(args.output)
            if args.format == "html":
                report_generator.export_to_html(report, str(output_path))
            else:
                report_generator.export_to_json(report, str(output_path))
            print_success(f"Report saved to {output_path}")
        else:
            print(format_output(report, format_type="json"))
        
    except Exception as e:
        print_error(f"Failed to generate report: {str(e)}")
        sys.exit(1)


def cmd_assess_tco(config: Config, args: argparse.Namespace):
    """Execute assess tco command."""
    try:
        print_info("Calculating TCO and ROI...")
        
        graph_store = GraphStore(
            uri=config.get("neo4j.uri"),
            user=config.get("neo4j.user"),
            password=config.get("neo4j.password")
        )
        
        profiler = Profiler(graph_store)
        tco_calculator = TCOCalculator(profiler)
        
        # Get repository metrics
        repository_metrics = profiler.profile_repository()
        
        # Calculate TCO
        tco_data = tco_calculator.calculate_tco(
            informatica_annual_cost=args.informatica_cost,
            repository_metrics=repository_metrics
        )
        
        # Calculate ROI if migration cost provided
        roi_data = None
        if args.migration_cost:
            annual_savings = tco_data.get('savings', {}).get('annual', 0)
            roi_data = tco_calculator.calculate_roi(
                migration_cost=args.migration_cost,
                annual_savings=annual_savings
            )
        
        # Estimate runtime improvements
        runtime_data = tco_calculator.estimate_runtime_improvement(
            repository_metrics=repository_metrics,
            current_runtime_hours=args.runtime_hours
        )
        
        # Generate comprehensive report
        report = tco_calculator.generate_cost_analysis_report(
            tco_data=tco_data,
            roi_data=roi_data,
            runtime_data=runtime_data
        )
        
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                import json
                json.dump(report, f, indent=2, default=str)
            print_success(f"TCO analysis saved to {output_path}")
        else:
            print(format_output(report, format_type="json"))
        
    except Exception as e:
        print_error(f"Failed to calculate TCO: {str(e)}")
        sys.exit(1)


def cmd_reconcile_mapping(config: Config, args: argparse.Namespace):
    """Execute reconcile mapping command."""
    try:
        print_info(f"Reconciling mapping: {args.mapping_name}")
        
        graph_store = GraphStore(
            uri=config.get("neo4j.uri"),
            user=config.get("neo4j.user"),
            password=config.get("neo4j.password")
        ) if config.get("neo4j.uri") else None
        
        reconciliation_engine = ReconciliationEngine(graph_store)
        
        # Parse connection configs
        source_connection = {}
        target_connection = {}
        
        if args.source_connection:
            if Path(args.source_connection).exists():
                with open(args.source_connection) as f:
                    import json
                    source_connection = json.load(f)
            else:
                import json
                source_connection = json.loads(args.source_connection)
        
        if args.target_connection:
            if Path(args.target_connection).exists():
                with open(args.target_connection) as f:
                    import json
                    target_connection = json.load(f)
            else:
                import json
                target_connection = json.loads(args.target_connection)
        
        result = reconciliation_engine.reconcile_mapping(
            mapping_name=args.mapping_name,
            source_connection=source_connection,
            target_connection=target_connection,
            comparison_method=args.method
        )
        
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                import json
                json.dump(result, f, indent=2, default=str)
            print_success(f"Reconciliation results saved to {output_path}")
        else:
            print(format_output(result, format_type="json"))
        
    except Exception as e:
        print_error(f"Failed to reconcile mapping: {str(e)}")
        sys.exit(1)


def cmd_reconcile_workflow(config: Config, args: argparse.Namespace):
    """Execute reconcile workflow command."""
    try:
        print_info(f"Reconciling workflow: {args.workflow_name}")
        
        graph_store = GraphStore(
            uri=config.get("neo4j.uri"),
            user=config.get("neo4j.user"),
            password=config.get("neo4j.password")
        ) if config.get("neo4j.uri") else None
        
        reconciliation_engine = ReconciliationEngine(graph_store)
        
        # Parse connection configs
        source_connection = {}
        target_connection = {}
        
        if args.source_connection:
            if Path(args.source_connection).exists():
                with open(args.source_connection) as f:
                    import json
                    source_connection = json.load(f)
            else:
                import json
                source_connection = json.loads(args.source_connection)
        
        if args.target_connection:
            if Path(args.target_connection).exists():
                with open(args.target_connection) as f:
                    import json
                    target_connection = json.load(f)
            else:
                import json
                target_connection = json.loads(args.target_connection)
        
        result = reconciliation_engine.reconcile_workflow(
            workflow_name=args.workflow_name,
            source_connection=source_connection,
            target_connection=target_connection,
            comparison_method=args.method
        )
        
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                import json
                json.dump(result, f, indent=2, default=str)
            print_success(f"Reconciliation results saved to {output_path}")
        else:
            print(format_output(result, format_type="json"))
        
    except Exception as e:
        print_error(f"Failed to reconcile workflow: {str(e)}")
        sys.exit(1)


def cmd_config_show(config: Config, args: argparse.Namespace):
    """Execute config show command."""
    print(format_output(config.config, format_type="json"))


def cmd_config_validate(config: Config, args: argparse.Namespace):
    """Execute config validate command."""
    try:
        config.validate()
        print_success("Configuration is valid")
    except ConfigurationError as e:
        print_error(f"Configuration validation failed: {str(e)}")
        sys.exit(1)


def cmd_upload(config: Config, args: argparse.Namespace, client: APIClient):
    """Execute upload command."""
    try:
        path = Path(args.path)
        if not path.exists():
            print_error(f"Path not found: {args.path}")
            sys.exit(1)
        
        if path.is_file():
            print_info(f"Uploading file: {args.path}")
            result = client.upload_file(str(path), args.session_id)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print_success(f"Uploaded: {result['filename']} (ID: {result['file_id']})")
                if result.get('session_id'):
                    print_info(f"Session ID: {result['session_id']}")
        else:
            print_info(f"Uploading directory: {args.path}")
            result = client.upload_directory(str(path), args.recursive, args.session_id)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print_success(f"Uploaded {result['count']} file(s)")
                print_info(f"Session ID: {result['session_id']}")
                print_info(f"File IDs: {', '.join(result['file_ids'][:5])}{'...' if len(result['file_ids']) > 5 else ''}")
    except Exception as e:
        print_error(f"Upload failed: {str(e)}")
        sys.exit(1)


def cmd_parse(config: Config, args: argparse.Namespace, client: APIClient):
    """Execute parse command."""
    try:
        if args.session_id:
            print_info(f"Parsing session: {args.session_id}")
            result = client.parse_session(args.session_id, args.type, args.enhance)
        elif args.target:
            path = Path(args.target)
            if path.is_file():
                print_info(f"Parsing file: {args.target}")
                result = client.parse_file(args.type, file_path=str(path), enhance=args.enhance)
            elif path.is_dir():
                print_info(f"Parsing directory: {args.target}")
                result = client.parse_directory(str(path), args.type, args.recursive, args.enhance)
            else:
                # Assume it's a file_id
                print_info(f"Parsing file ID: {args.target}")
                result = client.parse_file(args.type, file_id=args.target, enhance=args.enhance)
        else:
            print_error("Must provide target (file, directory, or --session-id)")
            sys.exit(1)
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if isinstance(result, dict) and "parsed" in result:
                print_success(f"Parsed {len(result['parsed'])} file(s)")
                if result.get('failed'):
                    print_warning(f"Failed: {len(result['failed'])} file(s)")
            else:
                print_success(f"Parsed: {result.get('mapping_name', 'unknown')}")
    except Exception as e:
        print_error(f"Parse failed: {str(e)}")
        sys.exit(1)


def cmd_enhance(config: Config, args: argparse.Namespace, client: APIClient):
    """Execute enhance command."""
    try:
        print_info(f"Enhancing model: {args.mapping_name}")
        result = client.enhance_model(args.mapping_name)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if result.get('enhanced'):
                print_success(f"Enhanced: {args.mapping_name}")
            else:
                print_warning(f"Enhancement skipped: {args.mapping_name}")
    except Exception as e:
        print_error(f"Enhance failed: {str(e)}")
        sys.exit(1)


def cmd_generate_code(config: Config, args: argparse.Namespace, client: APIClient):
    """Execute generate-code command."""
    try:
        print_info(f"Generating {args.type} code for: {args.mapping_name}")
        result = client.generate_code(args.type, args.mapping_name, args.output, args.review)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            for code_type, code_result in result.items():
                print_success(f"Generated {code_type}: {code_result['file']}")
                if code_result.get('quality_score'):
                    print_info(f"  Quality score: {code_result['quality_score']}")
    except Exception as e:
        print_error(f"Code generation failed: {str(e)}")
        sys.exit(1)


def cmd_review(config: Config, args: argparse.Namespace, client: APIClient):
    """Execute review command."""
    try:
        path = Path(args.path)
        if path.is_file():
            print_info(f"Reviewing: {args.path}")
            result = client.review_code(str(path), args.fix)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                review = result.get('review', {})
                print_success(f"Reviewed: {args.path}")
                if review.get('needs_fix'):
                    print_warning(f"Issues found: {len(review.get('issues', []))}")
                    if result.get('fixed'):
                        print_success(f"Fixed code saved: {result['fixed_file']}")
        else:
            print_error("Review command currently supports single files only")
            sys.exit(1)
    except Exception as e:
        print_error(f"Review failed: {str(e)}")
        sys.exit(1)


def cmd_fix(config: Config, args: argparse.Namespace, client: APIClient):
    """Execute fix command."""
    try:
        path = Path(args.path)
        if path.is_file():
            print_info(f"Fixing: {args.path}")
            result = client.fix_code(str(path), args.output)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                if result.get('fixed'):
                    print_success(f"Fixed code saved: {result['fixed_file']}")
                else:
                    print_warning("No fixes applied")
        else:
            print_error("Fix command currently supports single files only")
            sys.exit(1)
    except Exception as e:
        print_error(f"Fix failed: {str(e)}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Load configuration
    try:
        config = Config(config_path=args.config) if hasattr(args, 'config') and args.config else Config()
        config.validate()
    except ConfigurationError as e:
        print_error(f"Configuration error: {str(e)}")
        sys.exit(1)
    
    # Initialize API client
    workspace_dir = getattr(args, 'workspace_dir', 'workspace')
    api_url = getattr(args, 'api_url', None) or os.getenv('API_URL')
    client = APIClient(api_url=api_url, workspace_dir=workspace_dir)
    
    # Route to command handler
    try:
        if args.command == "upload":
            cmd_upload(config, args, client)
        elif args.command == "parse":
            cmd_parse(config, args, client)
        elif args.command == "enhance":
            cmd_enhance(config, args, client)
        elif args.command == "generate-code":
            cmd_generate_code(config, args, client)
        elif args.command == "review":
            cmd_review(config, args, client)
        elif args.command == "fix":
            cmd_fix(config, args, client)
        elif args.command == "assess":
            if args.assess_command == "profile":
                cmd_assess_profile(config, args)
            elif args.assess_command == "analyze":
                cmd_assess_analyze(config, args)
            elif args.assess_command == "waves":
                cmd_assess_waves(config, args)
            elif args.assess_command == "report":
                cmd_assess_report(config, args)
            elif args.assess_command == "tco":
                cmd_assess_tco(config, args)
            else:
                print_error("Invalid assess subcommand")
                sys.exit(1)
        elif args.command == "reconcile":
            if args.recon_command == "mapping":
                cmd_reconcile_mapping(config, args)
            elif args.recon_command == "workflow":
                cmd_reconcile_workflow(config, args)
            else:
                print_error("Invalid reconcile subcommand")
                sys.exit(1)
        elif args.command == "config":
            if args.config_command == "show":
                cmd_config_show(config, args)
            elif args.config_command == "validate":
                cmd_config_validate(config, args)
            else:
                print_error("Invalid config subcommand")
                sys.exit(1)
        else:
            print_error(f"Unknown command: {args.command}")
            sys.exit(1)
    except CLIError as e:
        print_error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        logger.exception("Unexpected error in CLI")
        sys.exit(1)


if __name__ == "__main__":
    main()

