# Code Review Templates

This directory contains comprehensive templates for conducting thorough, consistent code reviews across different programming languages and frameworks.

## 🎯 Purpose

Standardized code review templates ensure:
- **Consistent review quality** across team members and projects
- **Comprehensive coverage** of critical code quality aspects
- **Educational feedback** that helps developers improve their skills
- **Efficient review process** with structured checklists and criteria
- **Standards alignment** with organizational coding guidelines

## 📁 Available Templates

### Python Code Review Protocol
**Location**: `python/`

A comprehensive six-phase code review methodology specifically designed for Python applications, aligned with organizational coding standards.

**Phases:**
1. **Context & Architecture Review** - Project structure, documentation, and design
2. **Code Quality & Standards Review** - Style guidelines, formatting, and conventions
3. **Security & Error Handling Review** - Vulnerabilities, input validation, and error management
4. **Performance & Scalability Review** - Efficiency, optimization, and scale considerations
5. **Testing & Quality Assurance Review** - Test coverage, quality, and methodology
6. **Final Review & Recommendations** - Synthesis, assessment, and action plan

**Features:**
- Copy-paste ready prompts for AI-assisted reviews
- Detailed checklists for each phase
- Standards-based evaluation criteria
- Comprehensive README with step-by-step protocol
- Individual markdown files per phase for easy navigation
- Prioritized recommendations (Critical/High/Medium/Low)

**Time Investment:**
- Quick Review: 1-2 hours (checklists only)
- Standard Review: 3-4 hours (checklists + key prompts)
- Deep Review: 5-6 hours (full protocol with AI assistance)

**See**: [`python/README.md`](python/README.md) for complete details

---

## 🚀 Getting Started

### For Reviewers

1. **Select language/framework**: Navigate to appropriate directory (e.g., `python/`)
2. **Read the protocol**: Review the README for overview and methodology
3. **Follow phases sequentially**: Work through each phase in order
4. **Use checklists**: Verify compliance with each checklist item
5. **Copy prompts**: Use detailed prompts for AI-assisted analysis
6. **Document findings**: Record issues with specific examples and locations
7. **Provide recommendations**: Prioritize findings and suggest remediation

### For Development Teams

1. **Pre-review preparation**: Update documentation, run tests, fix obvious issues
2. **Understand standards**: Familiarize with coding standards referenced in templates
3. **Be receptive**: Embrace feedback as learning opportunities
4. **Discuss trade-offs**: Communicate constraints and decisions
5. **Track remediation**: Create tickets and monitor progress
6. **Schedule follow-ups**: Plan re-reviews after addressing findings

## 🛠 Template Philosophy

### Core Principles

- **Educational Approach**: Reviews teach "why," not just "what"
- **Standards-Aligned**: Based on organizational coding standards
- **Actionable Feedback**: Specific recommendations with remediation steps
- **Balanced Assessment**: Acknowledge strengths and improvements
- **AI-Assisted**: Prompts designed for use with AI coding assistants

### Review Outcomes

Each review provides:
- **Health Score**: Overall project assessment (1-5)
- **Deployment Recommendation**: Go/No-Go/Conditional decision
- **Prioritized Action Plan**: Issues categorized by severity
- **Technical Debt Quantification**: Effort estimates for improvements
- **Risk Assessment**: Identified risks with mitigation strategies

## 📈 Best Practices

### Using the Templates

- **Follow phases sequentially** for comprehensive coverage
- **Use AI assistance** with provided prompts for efficiency
- **Validate AI findings** against actual code with human judgment
- **Document thoroughly** with specific examples and line numbers
- **Prioritize actionably** based on severity and impact
- **Balance critique and praise** to maintain team morale

### Customizing for Your Project

- **Skip irrelevant phases** for focused reviews (e.g., security-only)
- **Adjust depth** based on available time and project criticality
- **Adapt criteria** to project-specific requirements
- **Extend templates** with organization-specific checks
- **Track effectiveness** and refine based on outcomes

## 🔄 Continuous Improvement

Templates evolve based on:
- **Team feedback**: Input from reviewers and developers
- **Industry standards**: Updates to best practices
- **Tool integration**: Enhancements for review workflows
- **Metric analysis**: Data-driven improvements
- **Lessons learned**: Real-world application insights

## 📝 Contributing

To contribute improvements:
1. **Test thoroughly**: Validate changes with actual reviews
2. **Document rationale**: Explain reasoning for modifications
3. **Ensure consistency**: Maintain structure and format
4. **Share learnings**: Contribute insights from usage
5. **Submit clearly**: Provide clear descriptions of changes

## 🔧 Future Templates

Planned additions:
- **JavaScript/TypeScript**: Frontend and Node.js applications
- **Java**: Enterprise application reviews
- **C#/.NET**: Windows and enterprise applications
- **Go**: Microservices and cloud-native applications
- **Rust**: Systems programming reviews

---

*Last Updated: October 2025*
*Current Templates: Python (complete)*