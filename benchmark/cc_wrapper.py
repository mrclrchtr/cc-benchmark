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
        self.chat_completion_call_hashes = []
        self.chat_completion_response_hashes = []
        self.ignore_mentions = set()
        self.partial_response_content = ""

        # Verify authentication
        self._verify_authentication()

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
            permission_mode="bypassPermissions",
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
        # Configure SDK options based on milestone specs
        options = ClaudeCodeOptions(
            model=self.model,
            permission_mode="bypassPermissions",  # Auto-approve for benchmark
            cwd=self.cwd,
            continue_conversation=True  # For session continuity
        )

        if self.verbose:
            print(f"[ClaudeCodeWrapper] Sending prompt to {self.model}")
            print(f"[ClaudeCodeWrapper] Working directory: {self.cwd}")

        result_text = ""
        messages_received = []
        
        try:
            async for message in query(prompt=prompt, options=options):
                messages_received.append(message)
                if self.verbose:
                    print(f"[ClaudeCodeWrapper] Received message: {type(message).__name__}")

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
            if self.verbose:
                print(f"[ClaudeCodeWrapper] Error: {e}")
                print(f"[ClaudeCodeWrapper] Messages received: {len(messages_received)}")
            raise

        if self.verbose:
            print(f"[ClaudeCodeWrapper] Response length: {len(result_text)} chars")

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
