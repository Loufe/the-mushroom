#!/usr/bin/env python3
"""
Pattern Registry - Dynamic pattern registration and management
"""

import logging
from typing import Dict, Type, Optional, List
from .base import Pattern

logger = logging.getLogger(__name__)


class PatternRegistry:
    """Central registry for all available patterns"""
    
    _instance = None
    _patterns: Dict[str, Type[Pattern]] = {}
    
    def __new__(cls):
        """Singleton pattern to ensure one registry"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._patterns = {}
        return cls._instance
    
    @classmethod
    def register(cls, name: str = None):
        """
        Decorator to register a pattern class
        
        Usage:
            @PatternRegistry.register("my_pattern")
            class MyPattern(Pattern):
                pass
        
        Or use class name if no name provided:
            @PatternRegistry.register()
            class MyPattern(Pattern):
                pass
        """
        def decorator(pattern_class: Type[Pattern]):
            pattern_name = name or pattern_class.__name__.lower().replace('pattern', '')
            
            # Ensure the class inherits from Pattern
            if not issubclass(pattern_class, Pattern):
                raise TypeError(f"{pattern_class.__name__} must inherit from Pattern base class")
            
            # Register the pattern
            cls._patterns[pattern_name] = pattern_class
            logger.info(f"Registered pattern: {pattern_name} ({pattern_class.__name__})")
            
            return pattern_class
        
        return decorator
    
    @classmethod
    def get_pattern(cls, name: str) -> Optional[Type[Pattern]]:
        """Get a pattern class by name"""
        return cls._patterns.get(name)
    
    @classmethod
    def create_pattern(cls, name: str, led_count: int, **kwargs) -> Optional[Pattern]:
        """Create a pattern instance by name"""
        pattern_class = cls.get_pattern(name)
        if pattern_class:
            return pattern_class(led_count, **kwargs)
        else:
            logger.error(f"Pattern '{name}' not found in registry")
            return None
    
    @classmethod
    def list_patterns(cls) -> List[str]:
        """Get list of all registered pattern names"""
        return list(cls._patterns.keys())
    
    @classmethod
    def get_all_patterns(cls) -> Dict[str, Type[Pattern]]:
        """Get all registered patterns"""
        return cls._patterns.copy()
    
    @classmethod
    def clear(cls):
        """Clear all registered patterns (mainly for testing)"""
        cls._patterns.clear()


# Create a single instance for easy import
registry = PatternRegistry()