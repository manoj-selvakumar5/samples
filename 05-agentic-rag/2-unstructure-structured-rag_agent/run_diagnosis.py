#!/usr/bin/env python3
"""
Simple runner for the Redshift Knowledge Base diagnostic tool
"""

from diagnose_redshift_kb_issues import RedshiftKBDiagnostic
import logging

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Configuration - these are the namespace ARNs you provided
    WORKING_NAMESPACE_ARN = "arn:aws:redshift-serverless:us-west-2:533267284022:namespace/9e7060fb-2754-41e4-8274-d50d95cbca1e"
    BROKEN_NAMESPACE_ARN = "arn:aws:redshift-serverless:us-west-2:533267284022:namespace/6e551b08-89e7-44e2-858f-8a445171f5b3"
    
    print("Starting Redshift Serverless Knowledge Base Diagnostic...")
    print(f"Working namespace: {WORKING_NAMESPACE_ARN}")
    print(f"Broken namespace: {BROKEN_NAMESPACE_ARN}")
    print("-" * 80)
    
    # Initialize diagnostic tool
    diagnostic = RedshiftKBDiagnostic()
    
    try:
        # Run comparison
        comparison = diagnostic.compare_namespaces(WORKING_NAMESPACE_ARN, BROKEN_NAMESPACE_ARN)
        
        # Generate and print report
        report = diagnostic.generate_report(comparison)
        print(report)
        
        # Save to file
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"diagnostic_report_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"\nReport saved to: {filename}")
        
    except Exception as e:
        print(f"Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 