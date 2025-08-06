"""Claude Code wrapper that mimics aider's Coder interface for benchmark integration."""
import asyncio
import os
from pathlib import Path
from typing import Dict

# Core imports - fail fast if critical dependencies missing
from claude_code_sdk import query, ClaudeCodeOptions
from models import ClaudeModel, lookup_model, get_available_models

# Required dependency for token counting and model validation
from anthropic import Anthropic

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
        
        # Initialize Anthropic client for accurate token counting (optional dependency)
        try:
            # Check if API key is available in environment
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if api_key:
                self.anthropic_client = Anthropic(api_key=api_key)
                if verbose:
                    print("ℹ️  [ClaudeCodeWrapper] Anthropic client initialized - accurate token counting enabled")
            else:
                self.anthropic_client = None
                if verbose:
                    print("ℹ️  [ClaudeCodeWrapper] ANTHROPIC_API_KEY not found - token counting will use fallback estimation")
        except Exception as e:
            self.anthropic_client = None
            if verbose:
                print(f"⚠️  [ClaudeCodeWrapper] Anthropic client initialization failed: {e} - using fallback estimation")

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

    def _estimate_tokens(self, text: str) -> int:
        """Count tokens using Anthropic SDK or character-based fallback.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count from Anthropic SDK or fallback estimate
        """
        if not text:
            return 0
            
        # Use Anthropic SDK if available
        if self.anthropic_client:
            try:
                count = self.anthropic_client.messages.count_tokens(
                    model=self.model,
                    messages=[{"role": "user", "content": text}]
                )
                print(f"[ClaudeCodeWrapper] SDK token count: {count.input_tokens}")
                return count.input_tokens
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  [ClaudeCodeWrapper] SDK token counting failed: {e}")

        if self.verbose:
            print("ℹ️  [ClaudeCodeWrapper] Using fallback character-based token counting")
        return max(1, len(text) // 3)

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on token counts and model pricing.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        # Approximate pricing for Claude models (as of 2025)
        # These are rough estimates - actual pricing may vary
        model_lower = self.model.lower()
        
        if 'sonnet' in model_lower:
            # Claude Sonnet pricing (approximate)
            input_cost_per_token = 3.0 / 1_000_000  # $3 per 1M input tokens
            output_cost_per_token = 15.0 / 1_000_000  # $15 per 1M output tokens
        elif 'haiku' in model_lower:
            # Claude Haiku pricing (approximate)
            input_cost_per_token = 0.25 / 1_000_000  # $0.25 per 1M input tokens
            output_cost_per_token = 1.25 / 1_000_000  # $1.25 per 1M output tokens
        elif 'opus' in model_lower:
            # Claude Opus pricing (approximate)
            input_cost_per_token = 15.0 / 1_000_000  # $15 per 1M input tokens
            output_cost_per_token = 75.0 / 1_000_000  # $75 per 1M output tokens
        else:
            # Default to Sonnet pricing
            input_cost_per_token = 3.0 / 1_000_000
            output_cost_per_token = 15.0 / 1_000_000
            
        return (input_tokens * input_cost_per_token) + (output_tokens * output_cost_per_token)

    def _update_metrics_from_message(self, message) -> None:
        """Extract and update metrics from SDK message objects.
        
        Args:
            message: Message object from Claude Code SDK
        """
        try:
            message_type = type(message).__name__
            
            # Handle ResultMessage - contains real cost and token metrics
            if message_type == 'ResultMessage':
                if hasattr(message, 'total_cost_usd'):
                    # Replace estimated cost with real cost from API
                    self.total_cost = getattr(message, 'total_cost_usd', 0.0)
                    if self.verbose:
                        print(f"[ClaudeCodeWrapper] Updated cost from ResultMessage: ${self.total_cost:.6f}")
                
                # Extract real token counts from usage data
                if hasattr(message, 'usage') and isinstance(message.usage, dict):
                    usage = message.usage
                    if 'input_tokens' in usage:
                        self.total_tokens_sent = usage['input_tokens']
                        if self.verbose:
                            print(f"[ClaudeCodeWrapper] Updated input tokens: {self.total_tokens_sent}")
                    if 'output_tokens' in usage:
                        self.total_tokens_received = usage['output_tokens']
                        if self.verbose:
                            print(f"[ClaudeCodeWrapper] Updated output tokens: {self.total_tokens_received}")
                    if 'cache_read_input_tokens' in usage:
                        self.total_thinking_tokens = usage['cache_read_input_tokens']
                        if self.verbose:
                            print(f"[ClaudeCodeWrapper] Updated thinking tokens: {self.total_thinking_tokens}")
            
            # Handle AssistantMessage - check for usage/billing info
            elif message_type == 'AssistantMessage':
                # Look for usage information in the message structure
                if hasattr(message, 'usage') and message.usage:
                    usage = message.usage
                    if hasattr(usage, 'input_tokens'):
                        input_tokens = getattr(usage, 'input_tokens', 0)
                        if input_tokens > 0:
                            # Replace estimated tokens with real API tokens
                            self.total_tokens_sent = input_tokens
                    if hasattr(usage, 'output_tokens'):
                        output_tokens = getattr(usage, 'output_tokens', 0)
                        if output_tokens > 0:
                            # Replace estimated tokens with real API tokens
                            self.total_tokens_received = output_tokens
                    if hasattr(usage, 'cache_read_input_tokens'):
                        # Claude's thinking tokens
                        self.total_thinking_tokens += getattr(usage, 'cache_read_input_tokens', 0)
                        
                # Check message.message if it has usage info
                elif hasattr(message, 'message') and hasattr(message.message, 'usage'):
                    usage = message.message.usage
                    if hasattr(usage, 'input_tokens'):
                        input_tokens = getattr(usage, 'input_tokens', 0)
                        if input_tokens > 0:
                            self.total_tokens_sent = input_tokens
                    if hasattr(usage, 'output_tokens'):
                        output_tokens = getattr(usage, 'output_tokens', 0)
                        if output_tokens > 0:
                            self.total_tokens_received = output_tokens
            
            # Check for error indicators in any message type
            if hasattr(message, 'error') and message.error:
                error_str = str(message.error).lower()
                if "context" in error_str and ("window" in error_str or "length" in error_str):
                    self.num_exhausted_context_windows += 1
                elif "malformed" in error_str or "invalid" in error_str:
                    self.num_malformed_responses += 1
                    
        except Exception as e:
            if self.verbose:
                print(f"[ClaudeCodeWrapper] Warning: Could not extract metrics from message: {e}")
                # Only show detailed debugging if DEBUG environment variable is set
                if os.environ.get('DEBUG'):
                    print(f"[ClaudeCodeWrapper] Message type: {type(message).__name__}")
                    print(f"[ClaudeCodeWrapper] Message attributes: {list(getattr(message, '__dict__', {}).keys())}")

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
        call_token_count = self._estimate_tokens(prompt)  # Better token estimation
        
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

        # Only add estimated tokens/cost if we didn't get real data from ResultMessage
        has_result_message = any(type(msg).__name__ == 'ResultMessage' for msg in messages_received)
        output_token_count = self._estimate_tokens(result_text)  # Better token estimation
        
        if not has_result_message:
            # Fallback to estimates if no ResultMessage received
            self.total_tokens_sent += call_token_count
            self.total_tokens_received += output_token_count
            
            # Use improved cost estimation based on model type
            call_cost = self._estimate_cost(call_token_count, output_token_count)
            self.total_cost += call_cost
        else:
            # We got real data from ResultMessage, use 0 for session tracking
            call_cost = 0
        
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
