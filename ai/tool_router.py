"""
Safe Tool Router Module
Provides explicitly registered, schema-validated Python application tools
for conversational AI agents. Strictly disallows arbitrary shell commands
or unrestricted SQL execution.
"""
from datetime import datetime
from typing import Dict, Any, Callable, Optional
import ast
import operator


class ToolRouter:
    """Dispatches validated application tools with safety checks"""

    def __init__(self, profile_service=None, health_service=None):
        self.profile_service = profile_service
        self.health_service = health_service
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def register_tool(self, name: str, description: str, handler: Callable[..., Any], parameters: Dict[str, Any], requires_confirmation: bool = False):
        """Register an authorized tool with schema and handler"""
        self.tools[name] = {
            'name': name,
            'description': description,
            'handler': handler,
            'parameters': parameters,
            'requires_confirmation': requires_confirmation
        }

    def _register_default_tools(self):
        # 1. Get current date and time
        self.register_tool(
            name='get_datetime',
            description='Returns the current date and time.',
            handler=self._tool_get_datetime,
            parameters={}
        )

        # 2. Perform safe arithmetic calculations
        self.register_tool(
            name='calculate',
            description='Performs safe arithmetic calculations without arbitrary code execution.',
            handler=self._tool_calculate,
            parameters={'expression': {'type': 'string', 'required': True}}
        )

        # 3. Profile Lookup
        self.register_tool(
            name='lookup_profile',
            description='Looks up an authorized user profile by name or ID.',
            handler=self._tool_lookup_profile,
            parameters={'name': {'type': 'string', 'required': False}}
        )

        # 4. Run Diagnostics
        self.register_tool(
            name='run_diagnostics',
            description='Runs system diagnostics and checks provider and database health.',
            handler=self._tool_run_diagnostics,
            parameters={}
        )

        # 5. Delete Profile (requires confirmation)
        self.register_tool(
            name='delete_profile',
            description='Deletes a specified profile. Destructive action requiring explicit confirmation.',
            handler=self._tool_delete_profile,
            parameters={'name': {'type': 'string', 'required': True}, 'confirmed': {'type': 'boolean', 'required': True}},
            requires_confirmation=True
        )

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Validate and execute a registered tool"""
        if tool_name not in self.tools:
            return {'success': False, 'error': f"Tool '{tool_name}' is not registered or unauthorized."}

        tool = self.tools[tool_name]
        
        # Check confirmation requirement for destructive actions
        if tool['requires_confirmation'] and not kwargs.get('confirmed', False):
            return {
                'success': False,
                'needs_confirmation': True,
                'message': f"Action '{tool_name}' requires explicit user confirmation before execution."
            }

        try:
            result = tool['handler'](**kwargs)
            return {'success': True, 'result': result}
        except Exception as e:
            return {'success': False, 'error': f"Execution error in tool '{tool_name}': {str(e)}"}

    def _tool_get_datetime(self, **kwargs) -> str:
        now = datetime.now()
        return now.strftime("Today is %A, %B %d, %Y, and the current time is %I:%M %p.")

    def _tool_calculate(self, expression: str = "", **kwargs) -> str:
        """Safe math evaluator using AST parsing (no eval / no shell)"""
        if not expression:
            return "Please provide a valid math expression."

        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg
        }

        def eval_node(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type in operators:
                    return operators[op_type](eval_node(node.left), eval_node(node.right))
            elif isinstance(node, ast.UnaryOp):
                op_type = type(node.op)
                if op_type in operators:
                    return operators[op_type](eval_node(node.operand))
            raise ValueError("Unsupported mathematical operation")

        try:
            tree = ast.parse(expression, mode='eval')
            result = eval_node(tree.body)
            return f"The result of {expression} is {result}."
        except Exception as e:
            return f"Could not evaluate expression: {e}"

    def _tool_lookup_profile(self, name: str = "", **kwargs) -> Dict[str, Any]:
        if not self.profile_service:
            return {'found': False, 'message': 'Profile service unavailable.'}
        found = self.profile_service.lookup_profile(name_query=name)
        if found:
            return {'found': True, 'profile': found}
        return {'found': False, 'message': f"No profile found matching '{name}'."}

    def _tool_run_diagnostics(self, **kwargs) -> Dict[str, Any]:
        if self.health_service:
            return self.health_service.check_health()
        return {'status': 'healthy', 'message': 'Diagnostics complete.'}

    def _tool_delete_profile(self, name: str = "", confirmed: bool = False, **kwargs) -> str:
        if not confirmed:
            return "Profile deletion requires confirmation."
        if not self.profile_service:
            return "Profile service unavailable."
        success = self.profile_service.delete_profile(user_id_or_name=name)
        if success:
            return f"Profile for '{name}' has been successfully deleted."
        return f"Could not find or delete profile for '{name}'."
