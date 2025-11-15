#!/usr/bin/env python3
"""
AI Conversation Logger for Quality Assurance
Logs all AI requests and responses for later review and quality improvement
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import hashlib


class AIConversationLogger:
    """Logs AI conversations (requests and responses) for QA purposes"""

    def __init__(self):
        # Configuration from environment variables
        self.enabled = os.getenv('AI_LOG_ENABLED', 'false').lower() in ['true', '1', 'yes']
        self.log_dir = os.getenv('AI_LOG_DIR', './logs/ai_conversations')
        self.log_format = os.getenv('AI_LOG_FORMAT', 'both')  # json, text, both
        self.max_prompt_length = int(os.getenv('AI_LOG_MAX_PROMPT', '5000'))
        self.max_response_length = int(os.getenv('AI_LOG_MAX_RESPONSE', '10000'))

        # Create log directory if logging is enabled
        if self.enabled:
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)

    def log_conversation(
        self,
        provider: str,
        prompt: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[str]:
        """
        Log an AI conversation with full context

        Args:
            provider: AI provider name (claude, codex, openai, etc.)
            prompt: The input prompt sent to the AI
            response: The AI's response
            metadata: Additional context (model, temperature, tokens, etc.)
            error: Error message if the call failed

        Returns:
            Path to the log file if logging is enabled, None otherwise
        """
        if not self.enabled:
            return None

        timestamp = datetime.datetime.now()
        conversation_id = self._generate_conversation_id(provider, timestamp)

        # Prepare the conversation data
        conversation_data = {
            'conversation_id': conversation_id,
            'timestamp': timestamp.isoformat(),
            'provider': provider,
            'prompt': self._truncate(prompt, self.max_prompt_length),
            'response': self._truncate(response, self.max_response_length) if response else None,
            'error': error,
            'metadata': metadata or {},
            'prompt_length': len(prompt),
            'response_length': len(response) if response else 0,
        }

        # Generate file paths
        date_prefix = timestamp.strftime('%Y%m%d_%H%M%S')
        base_filename = f"{date_prefix}_{provider}_{conversation_id[:8]}"

        log_files = []

        # Write JSON log
        if self.log_format in ['json', 'both']:
            json_path = os.path.join(self.log_dir, f"{base_filename}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            log_files.append(json_path)

        # Write human-readable text log
        if self.log_format in ['text', 'both']:
            text_path = os.path.join(self.log_dir, f"{base_filename}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(self._format_text_log(conversation_data))
            log_files.append(text_path)

        return log_files[0] if log_files else None

    def _generate_conversation_id(self, provider: str, timestamp: datetime.datetime) -> str:
        """Generate a unique conversation ID"""
        unique_string = f"{provider}_{timestamp.isoformat()}_{os.getpid()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text if it exceeds max_length"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + f"\n\n... [TRUNCATED: {len(text) - max_length} more characters]"

    def _format_text_log(self, data: Dict) -> str:
        """Format conversation data as human-readable text"""
        lines = [
            "=" * 80,
            f"AI CONVERSATION LOG",
            "=" * 80,
            f"Conversation ID: {data['conversation_id']}",
            f"Timestamp: {data['timestamp']}",
            f"Provider: {data['provider']}",
            f"Prompt Length: {data['prompt_length']} chars",
            f"Response Length: {data['response_length']} chars",
            "",
        ]

        # Add metadata
        if data['metadata']:
            lines.append("METADATA:")
            for key, value in data['metadata'].items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # Add prompt
        lines.extend([
            "-" * 80,
            "PROMPT:",
            "-" * 80,
            data['prompt'],
            "",
        ])

        # Add response or error
        if data['error']:
            lines.extend([
                "-" * 80,
                "ERROR:",
                "-" * 80,
                data['error'],
                "",
            ])
        elif data['response']:
            lines.extend([
                "-" * 80,
                "RESPONSE:",
                "-" * 80,
                data['response'],
                "",
            ])

        lines.append("=" * 80)
        return "\n".join(lines)

    def log_summary(self) -> Dict[str, Any]:
        """Get a summary of logged conversations"""
        if not self.enabled or not os.path.exists(self.log_dir):
            return {'enabled': False}

        log_files = list(Path(self.log_dir).glob('*.json'))

        summary = {
            'enabled': True,
            'log_directory': self.log_dir,
            'total_conversations': len(log_files),
            'log_format': self.log_format,
        }

        # Count by provider
        provider_counts = {}
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    data = json.load(f)
                    provider = data.get('provider', 'unknown')
                    provider_counts[provider] = provider_counts.get(provider, 0) + 1
            except Exception:
                pass

        summary['by_provider'] = provider_counts
        return summary


# Global logger instance
_logger_instance = None


def get_logger() -> AIConversationLogger:
    """Get or create the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AIConversationLogger()
    return _logger_instance


def log_ai_conversation(
    provider: str,
    prompt: str,
    response: str,
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function to log an AI conversation

    Args:
        provider: AI provider name (claude, codex, openai, etc.)
        prompt: The input prompt sent to the AI
        response: The AI's response
        metadata: Additional context (model, temperature, tokens, etc.)
        error: Error message if the call failed

    Returns:
        Path to the log file if logging is enabled, None otherwise
    """
    logger = get_logger()
    return logger.log_conversation(provider, prompt, response, metadata, error)


if __name__ == '__main__':
    # Test the logger
    print("AI Conversation Logger - Test Mode")
    print("=" * 80)

    logger = AIConversationLogger()

    if not logger.enabled:
        print("⚠️  Logging is DISABLED")
        print("To enable, set: export AI_LOG_ENABLED=true")
    else:
        print("✅ Logging is ENABLED")
        print(f"Log directory: {logger.log_dir}")
        print(f"Log format: {logger.log_format}")

        # Log a test conversation
        test_prompt = "Analyze this stock: RELIANCE - Reports Q1 profit of ₹5000 crores"
        test_response = json.dumps({
            "score": 85,
            "sentiment": "positive",
            "impact": "high",
            "recommendation": "BUY"
        }, indent=2)

        log_file = logger.log_conversation(
            provider='test',
            prompt=test_prompt,
            response=test_response,
            metadata={
                'model': 'test-model',
                'temperature': 0.2,
                'max_tokens': 1200
            }
        )

        if log_file:
            print(f"\n✅ Test conversation logged to: {log_file}")

        # Show summary
        summary = logger.log_summary()
        print("\nSummary:")
        print(json.dumps(summary, indent=2))
