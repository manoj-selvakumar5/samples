#!/usr/bin/env python3
"""
Redshift Serverless Knowledge Base Diagnostic Script

This script compares two Redshift Serverless namespaces to identify why one works 
with Bedrock Knowledge Base data ingestion and the other doesn't.

Usage:
    python diagnose_redshift_kb_issues.py
"""

import boto3
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RedshiftKBDiagnostic:
    def __init__(self, region: str = 'us-west-2'):
        """Initialize the diagnostic tool with AWS clients"""
        self.region = region
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        
        # Initialize AWS clients
        self.redshift_client = boto3.client('redshift-serverless', region_name=region)
        self.redshift_data_client = boto3.client('redshift-data', region_name=region)
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=region)
        self.iam_client = boto3.client('iam')
        
        logger.info(f"Initialized diagnostic tool for region: {region}")
        logger.info(f"Account ID: {self.account_id}")

    def extract_namespace_id(self, arn: str) -> str:
        """Extract namespace ID from ARN"""
        return arn.split('/')[-1]

    def get_namespace_details(self, namespace_id: str) -> Dict[str, Any]:
        """Get detailed information about a Redshift Serverless namespace"""
        try:
            # First try with the ID directly
            response = self.redshift_client.get_namespace(namespaceName=namespace_id)
            return response['namespace']
        except Exception as e:
            logger.error(f"Error getting namespace {namespace_id}: {e}")
            # Try to find the namespace by ID in the list
            try:
                response = self.redshift_client.list_namespaces()
                for ns in response.get('namespaces', []):
                    if ns.get('namespaceId') == namespace_id:
                        logger.info(f"Found namespace by ID: {ns.get('namespaceName')}")
                        return ns
                logger.error(f"Namespace {namespace_id} not found in list either")
                return {}
            except Exception as list_error:
                logger.error(f"Error listing namespaces: {list_error}")
                return {}

    def get_workgroups_for_namespace(self, namespace_name: str) -> List[Dict[str, Any]]:
        """Get all workgroups associated with a namespace"""
        try:
            response = self.redshift_client.list_workgroups()
            workgroups = []
            
            for wg in response.get('workgroups', []):
                if wg.get('namespaceName') == namespace_name:
                    # Get detailed workgroup info
                    detailed_wg = self.redshift_client.get_workgroup(
                        workgroupName=wg['workgroupName']
                    )
                    workgroups.append(detailed_wg['workgroup'])
            
            return workgroups
        except Exception as e:
            logger.error(f"Error getting workgroups for namespace {namespace_name}: {e}")
            return []

    def test_database_connectivity(self, workgroup_name: str, database_name: str) -> Dict[str, Any]:
        """Test database connectivity using Redshift Data API"""
        test_results = {
            'connectivity': False,
            'error': None,
            'tables_count': 0,
            'schemas': [],
            'sample_tables': []
        }
        
        try:
            # Test basic connectivity with a simple query
            logger.info(f"Testing connectivity to workgroup: {workgroup_name}, database: {database_name}")
            
            response = self.redshift_data_client.execute_statement(
                WorkgroupName=workgroup_name,
                Database=database_name,
                Sql="SELECT current_database(), current_user;"
            )
            
            statement_id = response['Id']
            
            # Wait for query completion
            max_wait = 30
            for _ in range(max_wait):
                status_response = self.redshift_data_client.describe_statement(Id=statement_id)
                status = status_response['Status']
                
                if status == 'FINISHED':
                    test_results['connectivity'] = True
                    break
                elif status == 'FAILED':
                    test_results['error'] = status_response.get('Error', 'Unknown error')
                    return test_results
                
                time.sleep(1)
            
            if test_results['connectivity']:
                # Get schema information
                self._get_schema_info(workgroup_name, database_name, test_results)
                
        except Exception as e:
            test_results['error'] = str(e)
            logger.error(f"Database connectivity test failed: {e}")
        
        return test_results

    def _get_schema_info(self, workgroup_name: str, database_name: str, test_results: Dict):
        """Get schema and table information"""
        try:
            # Get table count in public schema
            response = self.redshift_data_client.execute_statement(
                WorkgroupName=workgroup_name,
                Database=database_name,
                Sql="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
            )
            
            statement_id = response['Id']
            self._wait_for_statement(statement_id)
            
            result = self.redshift_data_client.get_statement_result(Id=statement_id)
            if result.get('Records'):
                test_results['tables_count'] = int(result['Records'][0][0]['longValue'])
            
            # Get sample table names
            if test_results['tables_count'] > 0:
                response = self.redshift_data_client.execute_statement(
                    WorkgroupName=workgroup_name,
                    Database=database_name,
                    Sql="SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5;"
                )
                
                statement_id = response['Id']
                self._wait_for_statement(statement_id)
                
                result = self.redshift_data_client.get_statement_result(Id=statement_id)
                test_results['sample_tables'] = [row[0]['stringValue'] for row in result.get('Records', [])]
                
        except Exception as e:
            logger.error(f"Error getting schema info: {e}")

    def _wait_for_statement(self, statement_id: str, max_wait: int = 30):
        """Wait for a Redshift Data API statement to complete"""
        for _ in range(max_wait):
            status_response = self.redshift_data_client.describe_statement(Id=statement_id)
            status = status_response['Status']
            
            if status == 'FINISHED':
                return
            elif status == 'FAILED':
                raise Exception(f"Statement failed: {status_response.get('Error', 'Unknown error')}")
            
            time.sleep(1)
        
        raise Exception("Statement timeout")

    def check_iam_permissions(self, workgroup_arn: str) -> Dict[str, Any]:
        """Check IAM permissions related to the workgroup"""
        permissions_check = {
            'bedrock_roles': [],
            'potential_issues': []
        }
        
        try:
            # Find roles that might be used with Bedrock
            paginator = self.iam_client.get_paginator('list_roles')
            
            for page in paginator.paginate():
                for role in page['Roles']:
                    role_name = role['RoleName']
                    
                    # Check if it's a Bedrock-related role
                    if 'bedrock' in role_name.lower() or 'knowledge' in role_name.lower():
                        permissions_check['bedrock_roles'].append({
                            'role_name': role_name,
                            'role_arn': role['Arn'],
                            'policies': self._get_role_policies(role_name, workgroup_arn)
                        })
            
        except Exception as e:
            logger.error(f"Error checking IAM permissions: {e}")
            permissions_check['potential_issues'].append(f"IAM check failed: {str(e)}")
        
        return permissions_check

    def _get_role_policies(self, role_name: str, workgroup_arn: str) -> Dict[str, Any]:
        """Get policies attached to a role and check Redshift permissions"""
        policy_info = {
            'attached_policies': [],
            'inline_policies': [],
            'has_redshift_access': False,
            'has_workgroup_access': False
        }
        
        try:
            # Get attached managed policies
            response = self.iam_client.list_attached_role_policies(RoleName=role_name)
            for policy in response.get('AttachedPolicies', []):
                policy_info['attached_policies'].append(policy['PolicyName'])
            
            # Get inline policies
            response = self.iam_client.list_role_policies(RoleName=role_name)
            for policy_name in response.get('PolicyNames', []):
                policy_info['inline_policies'].append(policy_name)
                        
        except Exception as e:
            logger.error(f"Error getting policies for role {role_name}: {e}")
        
        return policy_info

    def get_knowledge_bases_using_workgroup(self, workgroup_arn: str) -> List[Dict[str, Any]]:
        """Find Knowledge Bases that might be using this workgroup"""
        knowledge_bases = []
        
        try:
            response = self.bedrock_agent_client.list_knowledge_bases()
            
            for kb_summary in response.get('knowledgeBaseSummaries', []):
                kb_id = kb_summary['knowledgeBaseId']
                
                # Get detailed KB info
                kb_detail = self.bedrock_agent_client.get_knowledge_base(knowledgeBaseId=kb_id)
                kb_config = kb_detail['knowledgeBase']
                
                # Check if this KB uses the workgroup
                if self._kb_uses_workgroup(kb_config, workgroup_arn):
                    # Get data sources
                    data_sources = self.bedrock_agent_client.list_data_sources(knowledgeBaseId=kb_id)
                    
                    # Get recent ingestion jobs
                    ingestion_jobs = []
                    for ds in data_sources.get('dataSourceSummaries', []):
                        ds_id = ds['dataSourceId']
                        jobs = self.bedrock_agent_client.list_ingestion_jobs(
                            knowledgeBaseId=kb_id,
                            dataSourceId=ds_id,
                            maxResults=5
                        )
                        ingestion_jobs.extend(jobs.get('ingestionJobSummaries', []))
                    
                    knowledge_bases.append({
                        'knowledge_base_id': kb_id,
                        'name': kb_config.get('name'),
                        'status': kb_config.get('status'),
                        'data_sources_count': len(data_sources.get('dataSourceSummaries', [])),
                        'recent_ingestion_jobs': ingestion_jobs
                    })
                    
        except Exception as e:
            logger.error(f"Error getting Knowledge Bases: {e}")
        
        return knowledge_bases

    def _kb_uses_workgroup(self, kb_config: Dict, workgroup_arn: str) -> bool:
        """Check if a Knowledge Base configuration uses the specified workgroup"""
        try:
            config = kb_config.get('knowledgeBaseConfiguration', {})
            
            # Check for SQL configuration
            if config.get('type') == 'SQL':
                sql_config = config.get('sqlKnowledgeBaseConfiguration', {})
                redshift_config = sql_config.get('redshiftConfiguration', {})
                query_engine = redshift_config.get('queryEngineConfiguration', {})
                
                if query_engine.get('type') == 'SERVERLESS':
                    serverless_config = query_engine.get('serverlessConfiguration', {})
                    return serverless_config.get('workgroupArn') == workgroup_arn
            
            # Check storage configuration
            storage_config = kb_config.get('storageConfiguration', {})
            if storage_config.get('type') == 'RDS':
                rds_config = storage_config.get('rdsConfiguration', {})
                return rds_config.get('resourceArn') == workgroup_arn
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking KB workgroup usage: {e}")
            return False

    def diagnose_namespace(self, namespace_arn: str) -> Dict[str, Any]:
        """Perform comprehensive diagnosis of a namespace"""
        namespace_id = self.extract_namespace_id(namespace_arn)
        
        logger.info(f"Diagnosing namespace: {namespace_id}")
        
        diagnosis = {
            'namespace_arn': namespace_arn,
            'namespace_id': namespace_id,
            'namespace_details': {},
            'workgroups': [],
            'connectivity_tests': [],
            'iam_permissions': {},
            'knowledge_bases': [],
            'issues_found': [],
            'recommendations': []
        }
        
        # Get namespace details
        diagnosis['namespace_details'] = self.get_namespace_details(namespace_id)
        if not diagnosis['namespace_details']:
            diagnosis['issues_found'].append("Cannot retrieve namespace details")
            return diagnosis
        
        namespace_name = diagnosis['namespace_details'].get('namespaceName', namespace_id)
        
        # Get workgroups
        diagnosis['workgroups'] = self.get_workgroups_for_namespace(namespace_name)
        if not diagnosis['workgroups']:
            diagnosis['issues_found'].append("No workgroups found for this namespace")
            return diagnosis
        
        # Test connectivity for each workgroup
        for workgroup in diagnosis['workgroups']:
            wg_name = workgroup['workgroupName']
            
            # Try common database names
            databases = ['dev', 'test', 'prod']
            if diagnosis['namespace_details'].get('dbName'):
                databases.insert(0, diagnosis['namespace_details']['dbName'])
            
            for db_name in databases:
                connectivity_test = self.test_database_connectivity(wg_name, db_name)
                connectivity_test['workgroup_name'] = wg_name
                connectivity_test['database_name'] = db_name
                diagnosis['connectivity_tests'].append(connectivity_test)
                
                if connectivity_test['connectivity']:
                    break  # Found working database, no need to test others
        
        # Check IAM permissions for each workgroup
        for workgroup in diagnosis['workgroups']:
            wg_arn = f"arn:aws:redshift-serverless:{self.region}:{self.account_id}:workgroup/{workgroup['workgroupName']}"
            diagnosis['iam_permissions'][workgroup['workgroupName']] = self.check_iam_permissions(wg_arn)
            
            # Find Knowledge Bases using this workgroup
            kbs = self.get_knowledge_bases_using_workgroup(wg_arn)
            diagnosis['knowledge_bases'].extend(kbs)
        
        # Analyze issues
        self._analyze_issues(diagnosis)
        
        return diagnosis

    def _analyze_issues(self, diagnosis: Dict[str, Any]):
        """Analyze the diagnosis results and identify issues"""
        issues = diagnosis['issues_found']
        recommendations = diagnosis['recommendations']
        
        # Check connectivity
        working_connections = [test for test in diagnosis['connectivity_tests'] if test['connectivity']]
        if not working_connections:
            issues.append("No working database connections found")
            recommendations.append("Check if workgroups are running and databases exist")
        
        # Check for data
        has_data = any(test.get('tables_count', 0) > 0 for test in working_connections)
        if not has_data:
            issues.append("No tables found in public schema")
            recommendations.append("Ensure your data is loaded into the public schema")
        
        # Check IAM permissions
        has_bedrock_roles = any(
            len(perms.get('bedrock_roles', [])) > 0 
            for perms in diagnosis['iam_permissions'].values()
        )
        if not has_bedrock_roles:
            issues.append("No Bedrock-related IAM roles found")
            recommendations.append("Create IAM roles for Bedrock Knowledge Base access")
        
        # Check Knowledge Base usage
        if not diagnosis['knowledge_bases']:
            issues.append("No Knowledge Bases found using this workgroup")
            recommendations.append("Verify Knowledge Base configuration points to correct workgroup")
        else:
            # Check ingestion job status
            failed_jobs = []
            for kb in diagnosis['knowledge_bases']:
                for job in kb.get('recent_ingestion_jobs', []):
                    if job.get('status') == 'FAILED':
                        failed_jobs.append(job)
            
            if failed_jobs:
                issues.append(f"Found {len(failed_jobs)} failed ingestion jobs")
                recommendations.append("Check ingestion job failure reasons and fix underlying issues")

    def compare_namespaces(self, working_arn: str, broken_arn: str) -> Dict[str, Any]:
        """Compare two namespaces to identify differences"""
        logger.info("Starting namespace comparison...")
        
        working_diagnosis = self.diagnose_namespace(working_arn)
        broken_diagnosis = self.diagnose_namespace(broken_arn)
        
        comparison = {
            'working_namespace': working_diagnosis,
            'broken_namespace': broken_diagnosis,
            'key_differences': [],
            'recommendations': []
        }
        
        # Compare key aspects
        self._compare_connectivity(working_diagnosis, broken_diagnosis, comparison)
        self._compare_data_availability(working_diagnosis, broken_diagnosis, comparison)
        self._compare_iam_setup(working_diagnosis, broken_diagnosis, comparison)
        self._compare_knowledge_bases(working_diagnosis, broken_diagnosis, comparison)
        
        return comparison

    def _compare_connectivity(self, working: Dict, broken: Dict, comparison: Dict):
        """Compare connectivity between namespaces"""
        working_conn = any(test['connectivity'] for test in working['connectivity_tests'])
        broken_conn = any(test['connectivity'] for test in broken['connectivity_tests'])
        
        if working_conn and not broken_conn:
            comparison['key_differences'].append(
                "Working namespace has database connectivity, broken namespace does not"
            )
            comparison['recommendations'].append(
                "Check if broken namespace workgroups are running and accessible"
            )

    def _compare_data_availability(self, working: Dict, broken: Dict, comparison: Dict):
        """Compare data availability between namespaces"""
        working_tables = sum(test.get('tables_count', 0) for test in working['connectivity_tests'])
        broken_tables = sum(test.get('tables_count', 0) for test in broken['connectivity_tests'])
        
        if working_tables > 0 and broken_tables == 0:
            comparison['key_differences'].append(
                f"Working namespace has {working_tables} tables, broken namespace has none"
            )
            comparison['recommendations'].append(
                "Load data into the broken namespace's public schema"
            )

    def _compare_iam_setup(self, working: Dict, broken: Dict, comparison: Dict):
        """Compare IAM setup between namespaces"""
        working_roles = sum(
            len(perms.get('bedrock_roles', [])) 
            for perms in working['iam_permissions'].values()
        )
        broken_roles = sum(
            len(perms.get('bedrock_roles', [])) 
            for perms in broken['iam_permissions'].values()
        )
        
        if working_roles > broken_roles:
            comparison['key_differences'].append(
                f"Working namespace has {working_roles} Bedrock roles, broken has {broken_roles}"
            )
            comparison['recommendations'].append(
                "Ensure broken namespace has proper IAM roles for Bedrock access"
            )

    def _compare_knowledge_bases(self, working: Dict, broken: Dict, comparison: Dict):
        """Compare Knowledge Base setup between namespaces"""
        working_kbs = len(working['knowledge_bases'])
        broken_kbs = len(broken['knowledge_bases'])
        
        if working_kbs > 0 and broken_kbs == 0:
            comparison['key_differences'].append(
                f"Working namespace has {working_kbs} Knowledge Bases, broken has none"
            )
            comparison['recommendations'].append(
                "Create Knowledge Base configuration for broken namespace"
            )

    def generate_report(self, comparison: Dict[str, Any]) -> str:
        """Generate a comprehensive diagnostic report"""
        report = []
        report.append("=" * 80)
        report.append("REDSHIFT SERVERLESS KNOWLEDGE BASE DIAGNOSTIC REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Working namespace summary
        working = comparison['working_namespace']
        report.append("WORKING NAMESPACE ANALYSIS")
        report.append("-" * 40)
        report.append(f"ARN: {working['namespace_arn']}")
        report.append(f"Workgroups: {len(working['workgroups'])}")
        report.append(f"Connectivity Tests: {len([t for t in working['connectivity_tests'] if t['connectivity']])}/{len(working['connectivity_tests'])} passed")
        report.append(f"Total Tables: {sum(t.get('tables_count', 0) for t in working['connectivity_tests'])}")
        report.append(f"Knowledge Bases: {len(working['knowledge_bases'])}")
        report.append("")
        
        # Broken namespace summary
        broken = comparison['broken_namespace']
        report.append("BROKEN NAMESPACE ANALYSIS")
        report.append("-" * 40)
        report.append(f"ARN: {broken['namespace_arn']}")
        report.append(f"Workgroups: {len(broken['workgroups'])}")
        report.append(f"Connectivity Tests: {len([t for t in broken['connectivity_tests'] if t['connectivity']])}/{len(broken['connectivity_tests'])} passed")
        report.append(f"Total Tables: {sum(t.get('tables_count', 0) for t in broken['connectivity_tests'])}")
        report.append(f"Knowledge Bases: {len(broken['knowledge_bases'])}")
        report.append("")
        
        # Key differences
        if comparison['key_differences']:
            report.append("KEY DIFFERENCES")
            report.append("-" * 40)
            for diff in comparison['key_differences']:
                report.append(f"• {diff}")
            report.append("")
        
        # Issues found in broken namespace
        if broken['issues_found']:
            report.append("ISSUES FOUND IN BROKEN NAMESPACE")
            report.append("-" * 40)
            for issue in broken['issues_found']:
                report.append(f"• {issue}")
            report.append("")
        
        # Recommendations
        all_recommendations = comparison['recommendations'] + broken['recommendations']
        if all_recommendations:
            report.append("RECOMMENDATIONS")
            report.append("-" * 40)
            for rec in set(all_recommendations):  # Remove duplicates
                report.append(f"• {rec}")
            report.append("")
        
        # Detailed connectivity results
        report.append("DETAILED CONNECTIVITY RESULTS")
        report.append("-" * 40)
        
        for namespace_type, diagnosis in [("Working", working), ("Broken", broken)]:
            report.append(f"\n{namespace_type} Namespace:")
            for test in diagnosis['connectivity_tests']:
                status = "✓" if test['connectivity'] else "✗"
                report.append(f"  {status} {test['workgroup_name']}/{test['database_name']}")
                if test.get('error'):
                    report.append(f"    Error: {test['error']}")
                if test.get('tables_count', 0) > 0:
                    report.append(f"    Tables: {test['tables_count']}")
                    if test.get('sample_tables'):
                        report.append(f"    Sample: {', '.join(test['sample_tables'])}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main function to run the diagnostic"""
    # Configuration
    WORKING_NAMESPACE_ARN = "arn:aws:redshift-serverless:us-west-2:533267284022:namespace/9e7060fb-2754-41e4-8274-d50d95cbca1e"
    BROKEN_NAMESPACE_ARN = "arn:aws:redshift-serverless:us-west-2:533267284022:namespace/6e551b08-89e7-44e2-858f-8a445171f5b3"
    
    # Initialize diagnostic tool
    diagnostic = RedshiftKBDiagnostic()
    
    try:
        # Run comparison
        logger.info("Starting diagnostic comparison...")
        comparison = diagnostic.compare_namespaces(WORKING_NAMESPACE_ARN, BROKEN_NAMESPACE_ARN)
        
        # Generate and print report
        report = diagnostic.generate_report(comparison)
        print(report)
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"redshift_kb_diagnostic_report_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write(report)
        
        logger.info(f"Report saved to: {filename}")
        
        # Print JSON output for programmatic use
        print("\n" + "="*80)
        print("JSON OUTPUT (for programmatic use)")
        print("="*80)
        print(json.dumps({
            'working_issues': comparison['working_namespace']['issues_found'],
            'broken_issues': comparison['broken_namespace']['issues_found'],
            'key_differences': comparison['key_differences'],
            'recommendations': comparison['recommendations']
        }, indent=2))
        
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        raise


if __name__ == "__main__":
    main() 