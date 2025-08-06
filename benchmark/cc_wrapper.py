"""Claude Code wrapper that mimics aider's Coder interface for benchmark integration."""
import asyncio
import os
from pathlib import Path
from typing import Dict

from claude_code_sdk import query, ClaudeCodeOptions
from models import ClaudeModel, lookup_model, get_available_models


class ClaudeCodeWrapper:
    """Wrapper class that mimics aider's Coder interface using Claude Code SDK."""

    def __init__(self, model: str = ClaudeModel.get_default().value, verbose: bool = False):
        """Initialize the Claude Code wrapper.
        
        Args:
            model: Claude model to use (supports aider, benchmark, or Claude Code identifiers)
            verbose: Enable verbose logging
        """
        # Resolve model identifier using lookup
        try:
            self.model = lookup_model(model)
            if verbose:
                print(f"[ClaudeCodeWrapper] Resolved model '{model}' -> '{self.model}'")
        except ValueError as e:
            if verbose:
                print(f"[ClaudeCodeWrapper] Model resolution failed: {e}")
            # Fall back to original model name if lookup fails
            self.model = model
            
        self.verbose = verbose
        self.cwd = Path(os.getcwd())
        
        # Compatibility attributes with aider interface
        self.last_keyboard_interrupt = False
        self.total_cost = 0.0
        self.num_exhausted_context_windows = 0
        self.num_malformed_responses = 0
        self.total_tokens_sent = 0
        self.total_tokens_received = 0
        self.total_thinking_tokens = 0  # Track Claude's thinking tokens separately
        self.chat_completion_call_hashes = []
        self.chat_completion_response_hashes = []
        self.ignore_mentions = set()
        self.partial_response_content = ""
        
        # Additional metrics tracking
        self.api_calls_count = 0
        self.session_messages = []  # Store session history for continuity tracking

        # Verify authentication
        self._verify_authentication()

    def _get_permission_mode(self) -> str:
        """Get appropriate permission mode based on execution environment.
        
        Returns:
            Permission mode string for ClaudeCodeOptions
        """
        # Check if running as root user (Unix/Linux/macOS)
        try:
            is_root = os.geteuid() == 0
        except AttributeError:
            # Windows or other platforms without geteuid()
            is_root = False
            
        # Use acceptEdits for root (Docker compatibility) or bypassPermissions otherwise
        return "acceptEdits" if is_root else "bypassPermissions"

    def _verify_authentication(self) -> None:
        """Verify that Claude Code is logged in and available using SDK.
        
        Raises:
            RuntimeError: If Claude Code is not authenticated or available
        """
        try:
            # Test authentication with a minimal SDK query
            asyncio.run(self._test_authentication())
            
            if self.verbose:
                print("[ClaudeCodeWrapper] Authentication verified successfully")
                
        except Exception as e:
            # Handle various SDK authentication errors
            error_msg = str(e).lower()
            if "not authenticated" in error_msg or "login" in error_msg or "api key" in error_msg:
                raise RuntimeError(
                    "Claude Code is not authenticated. Please run 'claude' to log in or check your API key."
                )
            else:
                raise RuntimeError(f"Claude Code SDK verification failed: {e}")
    
    async def _test_authentication(self) -> None:
        """Test authentication with a minimal SDK query."""
        options = ClaudeCodeOptions(
            max_turns=1,
            model=ClaudeModel.HAIKU_3_5_LATEST.value,
            permission_mode=self._get_permission_mode(),
            cwd=self.cwd
        )
        
        # Use a minimal test prompt
        test_prompt = "Hello"
        
        # Try to execute a simple query
        message_received = False
        async for message in query(prompt=test_prompt, options=options):
            message_received = True
            if self.verbose:
                print(f"[ClaudeCodeWrapper] Auth test - received {type(message).__name__}")
            # We just need one successful message to verify auth works
            break
            
        if not message_received:
            raise RuntimeError("No response received from Claude Code SDK")

    def _update_metrics_from_message(self, message) -> None:
        """Extract and update metrics from SDK message objects.
        
        Args:
            message: Message object from Claude Code SDK
        """
        try:
            # Check for usage information in message attributes
            if hasattr(message, 'usage') and message.usage:
                usage = message.usage
                if hasattr(usage, 'input_tokens'):
                    self.total_tokens_sent += getattr(usage, 'input_tokens', 0)
                if hasattr(usage, 'output_tokens'):
                    self.total_tokens_received += getattr(usage, 'output_tokens', 0)
                if hasattr(usage, 'cache_read_input_tokens'):
                    # Claude's thinking tokens might be in cache reads
                    self.total_thinking_tokens += getattr(usage, 'cache_read_input_tokens', 0)
            
            # Check for cost information
            if hasattr(message, 'cost') and message.cost:
                if isinstance(message.cost, (int, float)):
                    self.total_cost += message.cost
                elif hasattr(message.cost, 'total'):
                    self.total_cost += getattr(message.cost, 'total', 0)
            
            # Check for error indicators
            if hasattr(message, 'error') and message.error:
                error_str = str(message.error).lower()
                if "context" in error_str and ("window" in error_str or "length" in error_str):
                    self.num_exhausted_context_windows += 1
                elif "malformed" in error_str or "invalid" in error_str:
                    self.num_malformed_responses += 1
                    
        except Exception as e:
            if self.verbose:
                print(f"[ClaudeCodeWrapper] Warning: Could not extract metrics from message: {e}")

    def run(self, with_message: str, preproc: bool = False) -> str:
        """Run a prompt through Claude Code SDK (sync interface mimicking aider).
        
        Args:
            with_message: The prompt to send to Claude
            preproc: Preprocessing flag (ignored for compatibility)
            
        Returns:
            The response from Claude Code
        """
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                # Create new loop if existing one is closed
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # No event loop in current thread, create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        try:
            return loop.run_until_complete(self._async_run(with_message))
        except Exception as e:
            if self.verbose:
                print(f"[ClaudeCodeWrapper] Exception in run(): {e}")
            raise

    async def _async_run(self, prompt: str) -> str:
        """Async implementation using Claude Code SDK.
        
        Args:
            prompt: The prompt to send to Claude
            
        Returns:
            The response from Claude Code
        """
        # Configure SDK options for benchmark execution
        options = ClaudeCodeOptions(
            model=self.model,
            permission_mode=self._get_permission_mode(),  # Auto-approve for benchmark
            cwd=self.cwd,
            continue_conversation=True  # For session continuity
        )

        if self.verbose:
            print(f"[ClaudeCodeWrapper] Sending prompt to {self.model}")
            print(f"[ClaudeCodeWrapper] Working directory: {self.cwd}")

        result_text = ""
        messages_received = []
        
        # Track this API call
        self.api_calls_count += 1
        call_token_count = len(prompt.split())  # Rough estimate for input tokens
        
        try:
            async for message in query(prompt=prompt, options=options):
                messages_received.append(message)
                if self.verbose:
                    print(f"[ClaudeCodeWrapper] Received message: {type(message).__name__}")

                # Extract and update metrics from each message
                self._update_metrics_from_message(message)

                # Handle different message types based on the actual SDK structure
                message_type = type(message).__name__
                
                if message_type == 'AssistantMessage':
                    # Extract text from assistant messages, filtering out tool blocks
                    if hasattr(message, 'content') and isinstance(message.content, list):
                        for content_block in message.content:
                            # Only extract TextBlock content, skip ToolUseBlock
                            if type(content_block).__name__ == 'TextBlock' and hasattr(content_block, 'text'):
                                result_text += content_block.text
                elif message_type == 'UserMessage':
                    # User messages typically contain tool results, skip for now
                    pass
                elif message_type == 'ResultMessage':
                    # Final result message might contain processed response
                    if hasattr(message, 'result') and message.result:
                        if isinstance(message.result, str):
                            result_text = message.result

        except Exception as e:
            # Track errors for metrics
            error_str = str(e).lower()
            if "context" in error_str and ("window" in error_str or "length" in error_str or "limit" in error_str):
                self.num_exhausted_context_windows += 1
            elif "malformed" in error_str or "invalid" in error_str or "parse" in error_str:
                self.num_malformed_responses += 1
                
            if self.verbose:
                print(f"[ClaudeCodeWrapper] Error: {e}")
                print(f"[ClaudeCodeWrapper] Messages received: {len(messages_received)}")
            raise

        # Estimate output tokens and update totals
        output_token_count = len(result_text.split())  # Rough estimate
        self.total_tokens_sent += call_token_count
        self.total_tokens_received += output_token_count
        
        # Estimate cost (rough approximation - Claude Sonnet pricing)
        # Input: ~$3/1M tokens, Output: ~$15/1M tokens (approximate)
        input_cost = (call_token_count / 1000000) * 3.0
        output_cost = (output_token_count / 1000000) * 15.0
        call_cost = input_cost + output_cost
        self.total_cost += call_cost
        
        # Update session tracking
        self.session_messages.append({
            'prompt': prompt[:100] + "..." if len(prompt) > 100 else prompt,
            'response_length': len(result_text),
            'tokens_in': call_token_count,
            'tokens_out': output_token_count,
            'cost': call_cost
        })
        
        # Update hashes for session tracking (simplified)
        import hashlib
        call_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        response_hash = hashlib.md5(result_text.encode()).hexdigest()[:8]
        self.chat_completion_call_hashes.append(call_hash)
        self.chat_completion_response_hashes.append(response_hash)
        
        if self.verbose:
            print(f"[ClaudeCodeWrapper] Response length: {len(result_text)} chars")
            print(f"[ClaudeCodeWrapper] Estimated tokens - In: {call_token_count}, Out: {output_token_count}")
            print(f"[ClaudeCodeWrapper] Estimated cost: ${call_cost:.6f}")
            print(f"[ClaudeCodeWrapper] Total cost so far: ${self.total_cost:.6f}")

        return result_text

    def set_cwd(self, cwd: Path) -> None:
        """Set the current working directory.
        
        Args:
            cwd: New working directory path
        """
        self.cwd = Path(cwd)
        if self.verbose:
            print(f"[ClaudeCodeWrapper] Changed working directory to: {self.cwd}")

    def show_announcements(self) -> None:
        """Show announcements (compatibility method for aider interface)."""
        pass

    def apply_updates(self) -> None:
        """Apply updates (compatibility method for aider interface)."""
        pass

    def get_file_mentions(self, text: str) -> set:
        """Get file mentions from text (compatibility method for aider interface)."""
        return set()

    @classmethod
    def get_supported_models(cls) -> Dict[str, str]:
        """Get all supported model mappings.
        
        Returns:
            Dictionary of supported model identifiers and their Claude Code equivalents
        """
        return get_available_models()
    
    @classmethod
    def resolve_model_name(cls, model_name: str) -> str:
        """Resolve a model name to Claude Code identifier.
        
        Args:
            model_name: Model name to resolve
            
        Returns:
            Claude Code model identifier
            
        Raises:
            ValueError: If model name cannot be resolved
        """
        return lookup_model(model_name)


# Factory function to match aider's Coder.create() pattern
def create_claude_code_wrapper(model: str = ClaudeModel.get_default().value,
                               verbose: bool = False) -> ClaudeCodeWrapper:
    """Factory function to create ClaudeCodeWrapper instance.
    
    Args:
        model: Claude model to use
        verbose: Enable verbose logging
        
    Returns:
        ClaudeCodeWrapper instance
    """
    return ClaudeCodeWrapper(model=model, verbose=verbose)


if __name__ == "__main__":
    from .models import print_available_models
    print_available_models()
