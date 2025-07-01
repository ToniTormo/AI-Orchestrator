"""
Project Coordinator

Main orchestrator for project analysis and implementation workflow.
Coordinates all services and manages the complete project lifecycle.
"""

from typing import Optional
from datetime import datetime

from src.utils.logging import setup_logger
from src.config import settings
from src.utils.exceptions_control import create_error, OrchestrationError

from src.application.factories.cli_context_factory import CLIContextFactory
from src.domain.models import (
    RepositoryAnalysisResult, 
    ViabilityAnalysisResult, 
    TaskExecutionResults
)
from src.cli.cli_enrich import display_viability_result, confirm_action, display_info, display_results_summary

class ProjectCoordinator:
    """Main coordinator for project analysis and implementation"""

    def __init__(self):
        """Initialize the project coordinator"""
        self.processed_task_plan = []  # Store processed tasks for display
        self.implementation_results = {}  # Store implementation results for display
        self.logger = setup_logger(
            "project.coordinator",
            settings.logging.module_levels.get("coordinator", settings.logging.level)
        )
        self.factory = CLIContextFactory()
        self.services = {}
        self.params = {}

    async def execute_project(
        self,
        repo_url: str,
        branch: str, 
        description: str,
        email: str,
        repos_path: Optional[str] = None
    ) -> Optional[bool]:
        """
        Execute complete project orchestration workflow
        
        Args:
            repo_url: Repository URL to process
            branch: Target branch for merge
            description: Description of requested changes  
            email: Email for notifications
            repos_path: Custom path for repositories (optional)
            
        Returns:
            Optional[bool]: 
                - True if successful and user confirmed
                - False if user declined during process
                - None if completed (for retry workflow)
        """
        workflow_result = None
        should_cleanup = True
        
        try:
            self.logger.info(f"[Coordinator] Starting project execution for: {repo_url}")
            
            # Initialize services using factory
            context_data = await self.factory.create_initialized_services(
                repo_url=repo_url,
                branch=branch,
                description=description,
                email=email,
                repos_path=repos_path
            )
            
            self.services = context_data['services']
            self.params = context_data['params']
            
            # Execute complete workflow and capture result
            workflow_result = await self._execute_complete_workflow()
            
            # Cleanup strategy based on result
            if workflow_result is False:
                should_cleanup = False
                self.logger.info("[Coordinator] Keeping services active for potential retry")
            
        except Exception as e:
            # On error, cleanup services
            should_cleanup = True
            raise create_error(OrchestrationError, f"Project execution failed: {str(e)}", "ProjectCoordinator")
            
        finally:
            # Only cleanup if we should (not on user decline for retry)
            if should_cleanup:
                await self.cleanup_services()
            
        return workflow_result
    
    async def _execute_complete_workflow(self):
        """Execute the complete project workflow with all stages"""
        try:
            # Stage 1: Repository Analysis (basic structure and technologies)
            analysis_result = await self._analyze_repository()
            
            # Stage 2: Basic Viability Analysis (quick technical assessment)
            viability_result = await self._analyze_basic_viability(analysis_result)
           
            # Stage 3: INTELLIGENT ANALYSIS WITH AI AGENT (enriched with context)
            ai_viability_result = await self._perform_intelligent_analysis(analysis_result, viability_result)
            
            # Stage 3.5: Show results to user and get confirmation
            if not await self._show_analysis_and_confirm(ai_viability_result):
                self.logger.info("[Coordinator] User declined to proceed with implementation")
                return False
            
            # Create and checkout a new feature branch for the work
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            feature_branch_name = f"feature/auto-update-{timestamp}"
            self.logger.info(f"[Coordinator] Creating feature branch: {feature_branch_name}")
            await self.services['git_service'].create_branch(
                repo_path=analysis_result.repo_path,
                branch_name=feature_branch_name
            )
            # Store the new branch name for later use in the PR
            self.params['feature_branch'] = feature_branch_name
            
            # Stage 4: Task Creation and Execution
            execution_results = await self._execute_tasks(analysis_result, ai_viability_result)
            
            # Stage 5: Review Request and Notification
            await self._create_review_request_and_notify(execution_results)
            
            # Stage 6: Display Final Results Summary
            await self._display_final_results(analysis_result, ai_viability_result, execution_results)
            
            self.logger.info("[Coordinator] Complete project workflow executed successfully")
            
        except Exception as e:
            raise create_error(OrchestrationError, f"Workflow execution failed: {str(e)}", "ProjectCoordinator")


    async def _analyze_repository(self) -> RepositoryAnalysisResult:
        """
        Analyze the repository structure and requirements
        
        Returns:
            RepositoryAnalysisResult with validated analysis data
        """
        try:
            self.logger.info("[Coordinator] Starting repository analysis")
            
            # Clone repository
            repo_path = await self.services['git_service'].clone_repository(
                url=self.params['repo_url'],
                branch=self.params['branch']
            )
            self.params['repo_path'] = repo_path # Store repo_path for later use
            
            # Get repository structure from git_service
            repo_structure = await self.services['git_service'].analyze_repository_structure(repo_path)
            
            # Analyze repository (complexity, technologies based on structure)
            analysis_data = await self.services['analysis_service'].analyze_repository(
                repo_path=repo_path,
                repo_structure=repo_structure
            )
            
            # Validate analysis result using Pydantic model - handles all validation
            analysis_result = RepositoryAnalysisResult(
                repo_path=str(repo_path),
                structure=analysis_data['structure'],
                complexity_score=analysis_data['complexity_score'],
                technologies=analysis_data['technologies'],
                estimated_hours=analysis_data['estimated_hours']
            )
            
            return analysis_result
            
        except Exception as e:
            raise create_error(OrchestrationError, f"Repository analysis failed: {str(e)}", "ProjectCoordinator")

    async def _analyze_basic_viability(self, analysis_result: RepositoryAnalysisResult) -> ViabilityAnalysisResult:
        """
        Perform basic viability analysis based on technical factors only
        
        Args:
            analysis_result: Result from repository analysis
            
        Returns:
            ViabilityAnalysisResult with basic viability assessment
        """
        try:
            self.logger.info("[Coordinator] Starting basic viability analysis")
            
            basic_viability = await self.services['analysis_service'].analyze_basic_viability(
                analysis_result=analysis_result
            )
            
            # Convert to ViabilityAnalysisResult and handle not viable case
            viability_result = ViabilityAnalysisResult(
                is_viable=basic_viability['is_viable'],
                confidence_score=basic_viability['confidence_score'],
                reasoning=basic_viability['reasoning']
            )
            
            if not viability_result.is_viable:
                await self._send_analysis_report_notification(viability_result)
                raise create_error(OrchestrationError, "Project is not viable based on initial analysis.", "ProjectCoordinator")
            
            self.logger.info(f"[Coordinator] Basic viability analysis completed - viable: {viability_result.is_viable}")
            return viability_result
            
        except Exception as e:
            raise create_error(OrchestrationError, f"Basic viability analysis failed: {str(e)}", "ProjectCoordinator")

    async def _perform_intelligent_analysis(self, analysis_result: RepositoryAnalysisResult, basic_viability: ViabilityAnalysisResult) -> ViabilityAnalysisResult:
        """
        Perform intelligent analysis using AI agent with context from basic analysis
        
        Args:
            analysis_result: Result from repository analysis
            basic_viability: Result from basic viability analysis
            
        Returns:
            ViabilityAnalysisResult with AI analysis results
        """
        try:
            self.logger.info("[Coordinator] Starting intelligent analysis with AI agent")
            
            # Pass simplified data to agent_analyzer
            intelligent_analysis = await self.services['agent_manager'].agents['analyzer'].analyze_project(
                description=self.params['description'],
                repo_path=analysis_result.repo_path,
                structure=analysis_result.structure,
                technologies=analysis_result.technologies,
                confidence_score=basic_viability.confidence_score
            )
            
            # Use AI decision directly (AI is smart enough to decide)
            ai_viability_score = intelligent_analysis.get('viability_score')
            ai_is_viable = ai_viability_score >= 20  # AI uses 0-100 scale, 60+ means viable
            
            # Create viability result from AI analysis
            ai_viability_result = ViabilityAnalysisResult(
                is_viable=ai_is_viable,
                confidence_score=ai_viability_score,
                tasks_steps=intelligent_analysis.get('tasks')
            )
            
            # Send notification with AI analysis result in every case
            await self._send_analysis_report_notification(ai_viability_result)
            
            if not ai_viability_result.is_viable:
                self.logger.warning(f"Project deemed not viable by AI: score {ai_viability_score}%. The user will be notified but the process continues as requested.")
            
            self.logger.info(f"[Coordinator] Intelligent analysis completed Mixed viability: {ai_viability_score}%")
            return ai_viability_result
            
        except Exception as e:
            raise create_error(OrchestrationError, f"Intelligent analysis failed: {str(e)}", "ProjectCoordinator")

    async def _show_analysis_and_confirm(self, ai_viability_result: ViabilityAnalysisResult) -> bool:
        """
        Show AI analysis results to user and get confirmation to proceed
        
        Args:
            ai_viability_result: AI analysis results with viability score and tasks
            
        Returns:
            bool: True if user confirms to proceed, False otherwise
        """
        try:
            self.logger.info("[Coordinator] Displaying analysis results to user")
            
            # Show viability score and tasks to user
            display_info("\n🤖 AI Analysis Complete!")
            display_viability_result(
                score=ai_viability_result.confidence_score,
                recommendations=ai_viability_result.tasks_steps
            )
            
            # Ask user for confirmation
            return confirm_action("\nDo you want to proceed with the implementation?")
            
        except Exception as e:
            raise create_error(OrchestrationError, f"Error showing analysis results: {str(e)}", "ProjectCoordinator")

    async def _execute_tasks(self, analysis_result: RepositoryAnalysisResult, intelligent_analysis: ViabilityAnalysisResult) -> TaskExecutionResults:
        """
        Execute project implementation tasks
        
        Args:
            analysis_result: Repository analysis results
            intelligent_analysis: AI analysis results
            
        Returns:
            TaskExecutionResults with execution summary
        """
        try:
            self.logger.info("[Coordinator] Starting task execution")
            
            execution_data = await self.services['task_manager'].execute_agent_tasks(
                repo_path=analysis_result.repo_path,
                technologies=analysis_result.technologies,
                ai_recommendations=intelligent_analysis.tasks_steps
            )

            # Store the processed task plan for display
            self.processed_task_plan = execution_data.get('task_plan', [])
            self.implementation_results = execution_data.get('implementation_results', {})

            # Generate a string summary from the list of modified files
            changes_list = execution_data.get('modified_files', [])
            if changes_list:
                summary_lines = ["Modified files:"]
                summary_lines.extend([f"- {item.get('file', 'N/A')} ({item.get('action', 'N/A')})" for item in changes_list])
                changes_summary_str = "\n".join(summary_lines)
            else:
                changes_summary_str = "No files were modified."
            
            # Validate execution results using Pydantic model
            execution_results = TaskExecutionResults(
                tasks_completed=execution_data['tasks_completed'],
                total_tasks=execution_data['total_tasks'],
                success_rate=execution_data['success_rate'],
                test_results=execution_data['test_results'],
                changes_summary=changes_summary_str
            )
            
            self.logger.info(f"[Coordinator] Task execution completed - success rate: {execution_results.success_rate}%")
            return execution_results
            
        except Exception as e:
            raise create_error(OrchestrationError, f"Task execution failed: {str(e)}", "ProjectCoordinator")

    async def _create_review_request_and_notify(self, execution_results: TaskExecutionResults):
        """
        Create review request and send notifications
        
        Args:
            execution_results: Results from task execution
        """
        try:
            self.logger.info("[Coordinator] Creating review request and sending notifications")

            # The branch was already created, now we commit, push and create the PR
            pr_data = await self.services['git_service'].create_merge_request_with_changes(
                repo_path=self.params['repo_path'],
                repo_url=self.params['repo_url'],
                feature_branch=self.params['feature_branch'],
                target_branch=self.params['branch'],
                commit_message="feat: Automated changes by AI Orchestrator",
                description=self._generate_pr_description(execution_results)
            )
            
            # Send notification email
            await self.services['notification_service'].send_completion_notification(
                email=self.params['email'],
                project_url=self.params['repo_url'],
                pr_url=pr_data.url,
                summary=execution_results.changes_summary
            )
            
            self.logger.info(f"[Coordinator] Review request created and notifications sent - PR: {pr_data.url}")
            
        except Exception as e:
            raise create_error(OrchestrationError, f"Review request creation failed: {str(e)}", "ProjectCoordinator")

    async def _send_analysis_report_notification(self, viability_result: ViabilityAnalysisResult):
        """Send notification with analysis results"""
        try:
            self.logger.info("[Coordinator] Sending analysis report notification")
            
            await self.services['notification_service'].send_viability_notification(
                email=self.params['email'],
                project_url=self.params['repo_url'],
                viability_result=viability_result
            )
            
            self.logger.info("[Coordinator] Analysis report notification sent")
            
        except Exception as e:
            raise create_error(OrchestrationError, f"Analysis report notification failed: {str(e)}", "ProjectCoordinator")

    def _generate_pr_description(self, execution_results: TaskExecutionResults) -> str:
        """
        Generate pull request description based on execution results
        
        Args:
            execution_results: Task execution results
            
        Returns:
            Formatted PR description
        """
        return f"""
                # AI Implementation Review

                ## Summary
                {execution_results.changes_summary}

                ## Statistics
                - **Tasks Completed**: {execution_results.tasks_completed}/{execution_results.total_tasks}
                - **Success Rate**: {execution_results.success_rate}%
                - **Test Results**: {execution_results.test_results}

                ## Review Required
                This implementation was generated by AI and requires human review before merging.

                Please review the changes carefully and ensure they meet your project requirements.
                        """.strip()

    async def cleanup_services(self):
        """Public method to cleanup all initialized services"""
        if self.services:
            try:
                await self.factory.shutdown_services(self.services)
                self.logger.info("[Coordinator] Services cleanup completed")
            except Exception as e:
                self.logger.error(f"[Coordinator] Error during cleanup: {str(e)}")
            finally:
                self.services = {}
                self.params = {} 
    async def _display_final_results(self, analysis_result: RepositoryAnalysisResult, viability_result: ViabilityAnalysisResult, execution_results: TaskExecutionResults):
        """
        Display final orchestration results to user
        
        Args:
            analysis_result: Repository analysis results
            viability_result: AI viability analysis results  
            execution_results: Task execution results
        """
        try:
            self.logger.info("[Coordinator] Displaying final orchestration results")
            
            # Prepare comprehensive results data for display
            results_data = {
                'viability_result': {
                    'status': 'viable' if viability_result.is_viable else 'not_viable',
                    'client_accepted': True,  # User confirmed to proceed
                    'score': viability_result.confidence_score
                },
                'task_plan': self.processed_task_plan,
                'implementation_results': self.implementation_results,
                'test_results': execution_results.test_results,
                'success': execution_results.success_rate >= 80,  # Consider 80%+ as success
                'execution_metadata': {
                    'repository': self.params['repo_url'],
                    'branch': self.params['feature_branch'],
                    'tasks_completed': f"{execution_results.tasks_completed}/{execution_results.total_tasks}",
                    'success_rate': f"{execution_results.success_rate}%"
                }
            }
            
            # Display comprehensive results summary
            display_results_summary(results_data, show_details=True)
            
        except Exception as e:
            self.logger.error(f"[Coordinator] Error displaying final results: {str(e)}")
            # Don't fail the workflow for display errors
            display_info("✅ Orchestration completed successfully!")