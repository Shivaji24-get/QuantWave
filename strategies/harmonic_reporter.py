"""
Harmonic Pattern Reporter Module
Handles export and reporting of harmonic pattern signals.
"""
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import csv

from .harmonic_detector import HarmonicPattern


class HarmonicReporter:
    """
    Reporter for harmonic pattern signals.
    
    Supports:
    - CSV export
    - JSON export
    - Markdown reports
    - Signal tracking
    """
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize Harmonic Reporter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self._signal_history: List[Dict[str, Any]] = []
    
    def export_to_csv(
        self,
        patterns: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Export patterns to CSV file.
        
        Args:
            patterns: List of pattern dictionaries
            filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if not patterns:
            return ""
        
        if filename is None:
            filename = f"harmonic_patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'symbol', 'pattern', 'direction', 'confidence',
                'entry_price', 'stop_loss', 'take_profit', 'risk_reward',
                'timestamp', 'ratios'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for pattern in patterns:
                writer.writerow({
                    'symbol': pattern.get('symbol', ''),
                    'pattern': pattern.get('name', ''),
                    'direction': pattern.get('direction', ''),
                    'confidence': pattern.get('confidence', 0),
                    'entry_price': pattern.get('entry_price', 0),
                    'stop_loss': pattern.get('stop_loss', 0),
                    'take_profit': pattern.get('take_profit', 0),
                    'risk_reward': pattern.get('risk_reward', 0),
                    'timestamp': pattern.get('timestamp', ''),
                    'ratios': json.dumps(pattern.get('ratios', {}))
                })
        
        return str(filepath)
    
    def export_to_json(
        self,
        patterns: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Export patterns to JSON file.
        
        Args:
            patterns: List of pattern dictionaries
            filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if not patterns:
            return ""
        
        if filename is None:
            filename = f"harmonic_patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                'exported_at': datetime.now().isoformat(),
                'total_patterns': len(patterns),
                'patterns': patterns
            }, f, indent=2)
        
        return str(filepath)
    
    def generate_markdown_report(
        self,
        scan_results: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a markdown report from scan results.
        
        Args:
            scan_results: List of scan result dictionaries
            filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to generated report
        """
        if filename is None:
            filename = f"harmonic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        filepath = self.output_dir / filename
        
        # Collect all patterns
        all_patterns = []
        for result in scan_results:
            if result.get('success') and result.get('patterns'):
                for pattern in result['patterns']:
                    pattern['symbol'] = result['symbol']
                    pattern['current_price'] = result.get('current_price', 0)
                    all_patterns.append(pattern)
        
        # Sort by confidence
        all_patterns.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Generate markdown
        md_content = f"# Harmonic Pattern Report\n\n"
        md_content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md_content += f"**Total Patterns Found:** {len(all_patterns)}\n\n"
        
        if all_patterns:
            md_content += "## Pattern Details\n\n"
            md_content += "| Rank | Symbol | Pattern | Direction | Confidence | Entry | SL | TP | R:R |\n"
            md_content += "|------|--------|---------|-----------|------------|-------|----|----|-----|\n"
            
            for rank, pattern in enumerate(all_patterns, 1):
                icon = "📈" if pattern.get('direction') == 'bullish' else "📉"
                md_content += f"| {rank} | {pattern.get('symbol')} | {icon} {pattern.get('name')} | {pattern.get('direction').upper()} | {pattern.get('confidence', 0):.0%} | ₹{pattern.get('entry_price', 0):.2f} | ₹{pattern.get('stop_loss', 0):.2f} | ₹{pattern.get('take_profit', 0):.2f} | {pattern.get('risk_reward', 0):.2f} |\n"
        
        # Summary statistics
        bullish = len([p for p in all_patterns if p.get('direction') == 'bullish'])
        bearish = len([p for p in all_patterns if p.get('direction') == 'bearish'])
        
        md_content += "\n## Summary\n\n"
        md_content += f"- **Bullish Patterns:** {bullish}\n"
        md_content += f"- **Bearish Patterns:** {bearish}\n"
        
        if all_patterns:
            avg_confidence = sum(p.get('confidence', 0) for p in all_patterns) / len(all_patterns)
            md_content += f"- **Average Confidence:** {avg_confidence:.0%}\n"
        
        with open(filepath, 'w') as f:
            f.write(md_content)
        
        return str(filepath)
    
    def track_signal(self, signal: Dict[str, Any]):
        """
        Track a signal in history.
        
        Args:
            signal: Signal dictionary
        """
        signal['tracked_at'] = datetime.now().isoformat()
        self._signal_history.append(signal)
    
    def get_signal_history(self) -> List[Dict[str, Any]]:
        """
        Get signal history.
        
        Returns:
            List of tracked signals
        """
        return self._signal_history
    
    def export_signal_history(self, filename: Optional[str] = None) -> str:
        """
        Export signal history to JSON.
        
        Args:
            filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"signal_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                'exported_at': datetime.now().isoformat(),
                'total_signals': len(self._signal_history),
                'signals': self._signal_history
            }, f, indent=2)
        
        return str(filepath)
    
    def clear_history(self):
        """Clear signal history."""
        self._signal_history.clear()
