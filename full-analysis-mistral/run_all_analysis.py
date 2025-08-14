#!/usr/bin/env python3
"""
Comprehensive Analysis Runner
============================

This script runs all analysis scripts in the correct order, creates necessary directories,
and provides comprehensive reporting and error handling.

Usage:
    python run_all_analysis.py [--verbose] [--skip-errors]
    
Options:
    --verbose: Enable detailed output
    --skip-errors: Continue running other scripts if one fails
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime

class AnalysisRunner:
    def __init__(self, verbose=False, skip_errors=False):
        self.verbose = verbose
        self.skip_errors = skip_errors
        self.analysis_dir = Path(__file__).parent
        self.reports_dir = self.analysis_dir / "reports"
        self.results = []
        
        # Define the scripts to run in order
        self.scripts = [
            {
                "name": "Model Evaluation (Real Dataset)",
                "file": "model_evaluation_real.py",
                "description": "Evaluates model performance using real dataset and generates metrics"
            },
            {
                "name": "Statistical Analysis",
                "file": "statistical_analysis.py",
                "description": "Performs statistical analysis on moderation results"
            },
            {
                "name": "Experimental Design",
                "file": "experimental_design.py",
                "description": "Runs experimental design analysis"
            },
            {
                "name": "Academic Analysis",
                "file": "run_academic_analysis.py",
                "description": "Comprehensive academic analysis and reporting"
            },
            {
                "name": "Export for Dissertation",
                "file": "export_for_dissertation.py",
                "description": "Exports results in dissertation format"
            },
            {
                "name": "View Results",
                "file": "view_results.py",
                "description": "Displays and summarizes all results"
            }
        ]
    
    def setup_directories(self):
        """Create necessary directories"""
        directories = [
            self.reports_dir,
            self.reports_dir / "figures",
            self.reports_dir / "data",
            self.reports_dir / "exports",
            self.analysis_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            if self.verbose:
                print(f"✓ Created/verified directory: {directory}")
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        try:
            import matplotlib
            import pandas
            import numpy
            import seaborn
            import scipy
            if self.verbose:
                print("✓ All required dependencies are available")
            return True
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("Please install requirements: pip install -r requirements.txt")
            return False
    
    def run_script(self, script_info):
        """Run a single analysis script"""
        script_name = script_info["name"]
        script_file = script_info["file"]
        script_path = self.analysis_dir / script_file
        
        if not script_path.exists():
            return {
                "name": script_name,
                "file": script_file,
                "status": "SKIPPED",
                "message": f"Script file not found: {script_file}",
                "duration": 0
            }
        
        print(f"\n{'='*60}")
        print(f"Running: {script_name}")
        print(f"File: {script_file}")
        print(f"Description: {script_info['description']}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Change to analysis directory to ensure relative paths work
            original_cwd = os.getcwd()
            os.chdir(self.analysis_dir)
            
            # Run the script
            result = subprocess.run(
                [sys.executable, script_file],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                status = "SUCCESS"
                message = "Completed successfully"
                if self.verbose and result.stdout:
                    print("STDOUT:", result.stdout)
            else:
                status = "FAILED"
                message = f"Exit code: {result.returncode}"
                if result.stderr:
                    message += f"\nError: {result.stderr}"
                print(f"❌ {script_name} failed:")
                print(f"   Exit code: {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr}")
            
            return {
                "name": script_name,
                "file": script_file,
                "status": status,
                "message": message,
                "duration": duration,
                "stdout": result.stdout if self.verbose else "",
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "name": script_name,
                "file": script_file,
                "status": "TIMEOUT",
                "message": "Script timed out after 5 minutes",
                "duration": time.time() - start_time
            }
        except Exception as e:
            return {
                "name": script_name,
                "file": script_file,
                "status": "ERROR",
                "message": str(e),
                "duration": time.time() - start_time
            }
        finally:
            os.chdir(original_cwd)
    
    def generate_summary_report(self):
        """Generate a summary report of all script executions"""
        report_path = self.reports_dir / f"analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w') as f:
            f.write("MODERATION SYSTEM ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Scripts: {len(self.results)}\n\n")
            
            # Summary statistics
            successful = sum(1 for r in self.results if r["status"] == "SUCCESS")
            failed = sum(1 for r in self.results if r["status"] == "FAILED")
            skipped = sum(1 for r in self.results if r["status"] == "SKIPPED")
            errors = sum(1 for r in self.results if r["status"] == "ERROR")
            timeouts = sum(1 for r in self.results if r["status"] == "TIMEOUT")
            
            f.write("SUMMARY STATISTICS:\n")
            f.write(f"  ✓ Successful: {successful}\n")
            f.write(f"  ❌ Failed: {failed}\n")
            f.write(f"  ⏭️  Skipped: {skipped}\n")
            f.write(f"  🚫 Errors: {errors}\n")
            f.write(f"  ⏰ Timeouts: {timeouts}\n\n")
            
            # Detailed results
            f.write("DETAILED RESULTS:\n")
            f.write("-" * 50 + "\n")
            
            for result in self.results:
                f.write(f"\nScript: {result['name']}\n")
                f.write(f"File: {result['file']}\n")
                f.write(f"Status: {result['status']}\n")
                f.write(f"Duration: {result['duration']:.2f} seconds\n")
                f.write(f"Message: {result['message']}\n")
                
                if result.get('stderr'):
                    f.write(f"Error Details: {result['stderr']}\n")
                
                f.write("-" * 30 + "\n")
        
        print(f"\n📊 Summary report saved to: {report_path}")
        return report_path
    
    def run_all(self):
        """Run all analysis scripts"""
        print("🚀 Starting Moderation System Analysis")
        print(f"Analysis Directory: {self.analysis_dir}")
        print(f"Reports Directory: {self.reports_dir}")
        
        # Setup
        print("\n📁 Setting up directories...")
        self.setup_directories()
        
        print("\n🔍 Checking dependencies...")
        if not self.check_dependencies():
            return False
        
        # Run scripts
        print(f"\n🏃 Running {len(self.scripts)} analysis scripts...")
        
        for i, script_info in enumerate(self.scripts, 1):
            print(f"\n[{i}/{len(self.scripts)}] Processing: {script_info['name']}")
            
            result = self.run_script(script_info)
            self.results.append(result)
            
            # Print immediate result
            status_emoji = {
                "SUCCESS": "✅",
                "FAILED": "❌", 
                "SKIPPED": "⏭️",
                "ERROR": "🚫",
                "TIMEOUT": "⏰"
            }
            
            emoji = status_emoji.get(result["status"], "❓")
            print(f"{emoji} {result['name']}: {result['status']} ({result['duration']:.2f}s)")
            
            if result["status"] in ["FAILED", "ERROR"] and not self.skip_errors:
                print(f"\n🛑 Stopping execution due to error in {result['name']}")
                print(f"Use --skip-errors flag to continue despite errors")
                break
        
        # Generate summary
        print(f"\n📊 Generating summary report...")
        summary_path = self.generate_summary_report()
        
        # Final summary
        successful = sum(1 for r in self.results if r["status"] == "SUCCESS")
        total = len(self.results)
        
        print(f"\n🎉 Analysis Complete!")
        print(f"✅ {successful}/{total} scripts completed successfully")
        print(f"📁 Reports saved in: {self.reports_dir}")
        print(f"📄 Summary report: {summary_path}")
        
        return successful == total

def main():
    parser = argparse.ArgumentParser(description="Run all moderation system analysis scripts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--skip-errors", "-s", action="store_true", help="Continue running scripts even if some fail")
    
    args = parser.parse_args()
    
    runner = AnalysisRunner(verbose=args.verbose, skip_errors=args.skip_errors)
    success = runner.run_all()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
