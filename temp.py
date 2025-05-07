#!/usr/bin/env python3
"""
CVE Report Generator
-------------------
Generates visual reports from CVE data in either JSON or CSV format.
"""

import json
import csv
import os
import argparse
import datetime
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from typing import Dict, List, Any, Union


class CVEReportGenerator:
    """Class for generating visual reports from CVE data."""
    
    def __init__(self, input_file: str, output_dir: str = "reports"):
        """Initialize the report generator.
        
        Args:
            input_file: Path to the input JSON or CSV file
            output_dir: Directory where reports will be saved
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.data = []
        self.report_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def load_data(self) -> None:
        """Load data from either JSON or CSV file."""
        file_ext = os.path.splitext(self.input_file)[1].lower()
        
        if file_ext == '.json':
            self._load_json()
        elif file_ext == '.csv':
            self._load_csv()
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Use JSON or CSV.")
    
    def _load_json(self) -> None:
        """Load data from JSON file."""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle both single CVE object and array of CVEs
            if isinstance(data, dict):
                self.data = [data]
            else:
                self.data = data
    
    def _load_csv(self) -> None:
        """Load data from CSV file and convert to schema format."""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                cve_obj = {
                    "id": row.get("id", ""),
                    "status": row.get("status", ""),
                    "descriptions": {
                        "en": row.get("description_en", ""),
                        "es": row.get("description_es", "")
                    },
                    "cvss": {
                        "2": [],
                        "3": [],
                        "3.1": [],
                        "4": []
                    },
                    "cwe": row.get("cwe", "").split(",") if row.get("cwe") else [],
                    "cpe": []
                }
                
                # Add CPE data if present
                if row.get("cpe_criteria"):
                    cpe_obj = {
                        "criteria": row.get("cpe_criteria", ""),
                        "minVerIncluding": row.get("minVerIncluding", ""),
                        "maxVerIncluding": row.get("maxVerIncluding", ""),
                        "minVerExcluding": row.get("minVerExcluding", ""),
                        "maxVerExcluding": row.get("maxVerExcluding", "")
                    }
                    cve_obj["cpe"].append(cpe_obj)
                
                # Handle CVSS v3 data
                if row.get("cvss3_source"):
                    cvss3_obj = {
                        "source": row.get("cvss3_source", ""),
                        "score": {
                            "exploitability": int(float(row.get("cvss3_exploitability", 0))),
                            "impact": int(float(row.get("cvss3_impact", 0))),
                            "base": int(float(row.get("cvss3_base", 0)))
                        },
                        "impact": {
                            "C": row.get("cvss3_C", "?"),
                            "I": row.get("cvss3_I", "?"),
                            "A": row.get("cvss3_A", "?")
                        },
                        "baseSeverity": row.get("cvss3_baseSeverity", "?"),
                        "vectorString": row.get("cvss3_vectorString", "?"),
                        "attackVector": row.get("cvss3_attackVector", "?"),
                        "attackComplexity": row.get("cvss3_attackComplexity", "?"),
                        "privilegesRequired": row.get("cvss3_privilegesRequired", "?"),
                        "userInteraction": row.get("cvss3_userInteraction", "?")
                    }
                    cve_obj["cvss"]["3"].append(cvss3_obj)
                
                self.data.append(cve_obj)
    
    def generate_reports(self) -> None:
        """Generate all reports."""
        if not self.data:
            print("No data loaded. Please load data first.")
            return
        
        self._generate_summary_report()
        self._generate_severity_distribution()
        self._generate_attack_vector_distribution()
        self._generate_attack_complexity_distribution()
        self._generate_user_interaction_distribution()
        self._generate_cia_impact_analysis()
        self._generate_combined_report()
        
        print(f"Reports generated successfully in '{self.output_dir}' directory")
    
    def _extract_cvss3_data(self) -> List[Dict]:
        """Extract all CVSS v3 data entries from loaded CVEs."""
        cvss3_entries = []
        
        for cve in self.data:
            for entry in cve.get("cvss", {}).get("3", []):
                # Add the CVE ID to the entry for reference
                entry["cve_id"] = cve["id"]
                cvss3_entries.append(entry)
        
        return cvss3_entries
    
    def _generate_summary_report(self) -> None:
        """Generate a summary report with basic statistics."""
        cvss3_data = self._extract_cvss3_data()
        
        # Count by status
        status_counter = Counter(cve["status"] for cve in self.data)
        
        # Create the figure and subplot
        plt.figure(figsize=(10, 6))
        plt.bar(status_counter.keys(), status_counter.values(), color='steelblue')
        plt.title('CVE Status Distribution', fontsize=16)
        plt.xlabel('Status', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(os.path.join(self.output_dir, 'status_distribution.png'), dpi=300)
        plt.close()
        
        # Generate summary text
        with open(os.path.join(self.output_dir, 'summary_report.txt'), 'w') as f:
            f.write(f"CVE Analysis Summary Report\n")
            f.write(f"Generated on: {self.report_date}\n")
            f.write(f"{'='*50}\n\n")
            
            f.write(f"Total CVEs analyzed: {len(self.data)}\n")
            f.write(f"CVEs with CVSS v3 data: {len(cvss3_data)}\n\n")
            
            f.write("Status Distribution:\n")
            for status, count in status_counter.items():
                f.write(f"  - {status}: {count} ({count/len(self.data)*100:.1f}%)\n")
    
    def _generate_severity_distribution(self) -> None:
        """Generate a chart showing the distribution of base severity levels."""
        cvss3_data = self._extract_cvss3_data()
        
        if not cvss3_data:
            print("No CVSS v3 data found for severity analysis")
            return
        
        severity_counter = Counter(entry.get("baseSeverity", "?") for entry in cvss3_data)
        
        # Create pie chart for severity distribution
        plt.figure(figsize=(10, 7))
        colors = {
            "LOW": "green", 
            "MEDIUM": "gold", 
            "HIGH": "red", 
            "?": "gray"
        }
        
        labels = [f"{sev} ({count})" for sev, count in severity_counter.items()]
        sizes = severity_counter.values()
        pie_colors = [colors.get(sev, "blue") for sev in severity_counter.keys()]
        
        plt.pie(
            sizes, 
            labels=labels, 
            colors=pie_colors,
            autopct='%1.1f%%', 
            startangle=90,
            shadow=True,
            explode=[0.05] * len(severity_counter)
        )
        plt.axis('equal')
        plt.title('CVE Base Severity Distribution', fontsize=16)
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(os.path.join(self.output_dir, 'severity_distribution.png'), dpi=300)
        plt.close()
    
    def _generate_attack_vector_distribution(self) -> None:
        """Generate a chart showing the distribution of attack vectors."""
        cvss3_data = self._extract_cvss3_data()
        
        if not cvss3_data:
            print("No CVSS v3 data found for attack vector analysis")
            return
        
        vector_counter = Counter(entry.get("attackVector", "?") for entry in cvss3_data)
        
        # Create horizontal bar chart
        plt.figure(figsize=(10, 6))
        colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]
        
        keys = list(vector_counter.keys())
        values = list(vector_counter.values())
        
        # Calculate percentages
        total = sum(values)
        percentages = [(v/total)*100 for v in values]
        
        # Sort by frequency
        sorted_items = sorted(zip(keys, values, percentages), key=lambda x: x[1], reverse=True)
        keys = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        percentages = [item[2] for item in sorted_items]
        
        plt.barh(keys, values, color=colors[:len(keys)])
        
        # Add value and percentage labels
        for i, (value, percentage) in enumerate(zip(values, percentages)):
            plt.text(value + 0.5, i, f"{value} ({percentage:.1f}%)", va='center')
        
        plt.title('Attack Vector Distribution', fontsize=16)
        plt.xlabel('Count', fontsize=12)
        plt.ylabel('Attack Vector', fontsize=12)
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(os.path.join(self.output_dir, 'attack_vector_distribution.png'), dpi=300)
        plt.close()
    
    def _generate_attack_complexity_distribution(self) -> None:
        """Generate a chart showing the distribution of attack complexity."""
        cvss3_data = self._extract_cvss3_data()
        
        if not cvss3_data:
            print("No CVSS v3 data found for attack complexity analysis")
            return
        
        complexity_counter = Counter(entry.get("attackComplexity", "?") for entry in cvss3_data)
        
        # Create pie chart
        plt.figure(figsize=(10, 7))
        colors = {"LOW": "#e74c3c", "HIGH": "#2ecc71", "?": "#95a5a6"}
        
        labels = [f"{complexity} ({count})" for complexity, count in complexity_counter.items()]
        sizes = complexity_counter.values()
        pie_colors = [colors.get(complexity, "#3498db") for complexity in complexity_counter.keys()]
        
        plt.pie(
            sizes, 
            labels=labels, 
            colors=pie_colors,
            autopct='%1.1f%%', 
            startangle=90,
            shadow=True
        )
        plt.axis('equal')
        plt.title('Attack Complexity Distribution', fontsize=16)
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(os.path.join(self.output_dir, 'attack_complexity_distribution.png'), dpi=300)
        plt.close()
    
    def _generate_user_interaction_distribution(self) -> None:
        """Generate a chart showing whether user interaction is required."""
        cvss3_data = self._extract_cvss3_data()
        
        if not cvss3_data:
            print("No CVSS v3 data found for user interaction analysis")
            return
        
        interaction_counter = Counter(entry.get("userInteraction", "?") for entry in cvss3_data)
        
        # Create pie chart
        plt.figure(figsize=(10, 7))
        colors = {"NONE": "#e74c3c", "REQUIRED": "#2ecc71", "?": "#95a5a6"}
        
        labels = [f"{interaction} ({count})" for interaction, count in interaction_counter.items()]
        sizes = interaction_counter.values()
        pie_colors = [colors.get(interaction, "#3498db") for interaction in interaction_counter.keys()]
        
        plt.pie(
            sizes, 
            labels=labels, 
            colors=pie_colors,
            autopct='%1.1f%%', 
            startangle=90,
            shadow=True
        )
        plt.axis('equal')
        plt.title('User Interaction Requirement Distribution', fontsize=16)
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(os.path.join(self.output_dir, 'user_interaction_distribution.png'), dpi=300)
        plt.close()
    
    def _generate_cia_impact_analysis(self) -> None:
        """Generate a chart analyzing Confidentiality, Integrity, and Availability impacts."""
        cvss3_data = self._extract_cvss3_data()
        
        if not cvss3_data:
            print("No CVSS v3 data found for CIA impact analysis")
            return
        
        # Extract CIA impact data
        impacts = {"C": [], "I": [], "A": []}
        for entry in cvss3_data:
            for impact_type in impacts:
                impacts[impact_type].append(entry.get("impact", {}).get(impact_type, "?"))
        
        # Count impact levels for each type
        impact_counts = {}
        for impact_type, values in impacts.items():
            impact_counts[impact_type] = Counter(values)
        
        # Define impact levels and colors
        impact_levels = ["NONE", "PARTIAL", "COMPLETE", "?"]
        colors = ["#2ecc71", "#f39c12", "#e74c3c", "#95a5a6"]
        
        # Create grouped bar chart
        plt.figure(figsize=(12, 7))
        x = range(len(impact_levels))
        width = 0.25
        
        for i, (impact_type, counts) in enumerate(impact_counts.items()):
            values = [counts.get(level, 0) for level in impact_levels]
            plt.bar([pos + i*width for pos in x], values, width, label=f"{impact_type} Impact", alpha=0.8)
        
        plt.xlabel('Impact Level', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.title('CIA Impact Analysis', fontsize=16)
        plt.xticks([pos + width for pos in x], impact_levels)
        plt.legend()
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(os.path.join(self.output_dir, 'cia_impact_analysis.png'), dpi=300)
        plt.close()
    
    def _generate_combined_report(self) -> None:
        """Generate a combined HTML report with all charts."""
        report_path = os.path.join(self.output_dir, 'combined_report.html')
        
        cvss3_data = self._extract_cvss3_data()
        total_cves = len(self.data)
        cves_with_cvss3 = len(cvss3_data)
        
        # Calculate severity percentages
        severity_counter = Counter(entry.get("baseSeverity", "?") for entry in cvss3_data)
        total_with_severity = sum(severity_counter.values())
        severity_pct = {k: (v/total_with_severity*100) for k, v in severity_counter.items()}
        
        # Calculate attack vector percentages
        vector_counter = Counter(entry.get("attackVector", "?") for entry in cvss3_data)
        total_with_vector = sum(vector_counter.values())
        vector_pct = {k: (v/total_with_vector*100) for k, v in vector_counter.items()}
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CVE Security Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .summary-box {{
            background-color: #f9f9f9;
            border-left: 5px solid #3498db;
            padding: 15px;
            margin-bottom: 25px;
        }}
        .chart-container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            margin-bottom: 30px;
        }}
        .chart {{
            width: 48%;
            margin-bottom: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            padding: 15px;
        }}
        .chart img {{
            max-width: 100%;
            height: auto;
        }}
        .chart h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        table, th, td {{
            border: 1px solid #ddd;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        footer {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background-color: #f2f2f2;
            color: #555;
        }}
        .severity-high {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .severity-medium {{
            color: #f39c12;
            font-weight: bold;
        }}
        .severity-low {{
            color: #2ecc71;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>CVE Security Analysis Report</h1>
            <p>Generated on: {self.report_date}</p>
        </header>
        
        <div class="summary-box">
            <h2>Executive Summary</h2>
            <p>This report analyzes <strong>{total_cves}</strong> CVE entries, of which <strong>{cves_with_cvss3}</strong> contain CVSS v3 data.</p>
            
            <h3>Key Findings:</h3>
            <ul>
                {"".join([f'<li><span class="severity-{sev.lower()}">{sev}</span> severity vulnerabilities: {severity_counter.get(sev, 0)} ({severity_pct.get(sev, 0):.1f}%)</li>' for sev in ["HIGH", "MEDIUM", "LOW"] if sev in severity_counter])}
                {"".join([f'<li>Most common attack vector: <strong>{sorted(vector_counter.items(), key=lambda x: x[1], reverse=True)[0][0]}</strong> ({vector_pct.get(sorted(vector_counter.items(), key=lambda x: x[1], reverse=True)[0][0], 0):.1f}%)</li>' if vector_counter else ''])}
            </ul>
        </div>
        
        <div class="chart-container">
            <div class="chart">
                <h3>Severity Distribution</h3>
                <img src="severity_distribution.png" alt="Severity Distribution">
            </div>
            
            <div class="chart">
                <h3>Attack Vector Distribution</h3>
                <img src="attack_vector_distribution.png" alt="Attack Vector Distribution">
            </div>
            
            <div class="chart">
                <h3>Attack Complexity</h3>
                <img src="attack_complexity_distribution.png" alt="Attack Complexity Distribution">
            </div>
            
            <div class="chart">
                <h3>User Interaction Requirement</h3>
                <img src="user_interaction_distribution.png" alt="User Interaction Distribution">
            </div>
            
            <div class="chart">
                <h3>CIA Impact Analysis</h3>
                <img src="cia_impact_analysis.png" alt="CIA Impact Analysis">
            </div>
            
            <div class="chart">
                <h3>Status Distribution</h3>
                <img src="status_distribution.png" alt="Status Distribution">
            </div>
        </div>
        
        <h2>Top High Severity Vulnerabilities</h2>
        <table>
            <tr>
                <th>CVE ID</th>
                <th>Attack Vector</th>
                <th>Attack Complexity</th>
                <th>User Interaction</th>
                <th>Base Score</th>
            </tr>
            {"".join([
                f'<tr><td>{entry["cve_id"]}</td><td>{entry.get("attackVector", "?")}</td><td>{entry.get("attackComplexity", "?")}</td><td>{entry.get("userInteraction", "?")}</td><td>{entry.get("score", {}).get("base", "?")}</td></tr>'
                for entry in sorted([e for e in cvss3_data if e.get("baseSeverity") == "HIGH"], key=lambda x: x.get("score", {}).get("base", 0), reverse=True)[:10]
            ])}
        </table>
        
        <footer>
            <p>Report generated by CVE Report Generator</p>
        </footer>
    </div>
</body>
</html>
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """Parse command line arguments and run the report generator."""
    parser = argparse.ArgumentParser(description='Generate visual reports from CVE data.')
    parser.add_argument('input_file', help='Path to the input JSON or CSV file')
    parser.add_argument('-o', '--output-dir', default='reports', help='Directory where reports will be saved')
    
    args = parser.parse_args()
    
    # Create and run the report generator
    generator = CVEReportGenerator(args.input_file, args.output_dir)
    generator.load_data()
    generator.generate_reports()


if __name__ == "__main__":
    main()
