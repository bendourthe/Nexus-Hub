# Code Review Templates# Code Review Templates



Comprehensive templates for conducting thorough, consistent code reviews across different programming languages and frameworks.This directory contains comprehensive templates for conducting thorough, consistent code reviews across different programming languages and frameworks.



---## 🎯 Purpose



## 📂 Repository StructureStandardized code review templates ensure:

- **Consistent review quality** across team members and projects

```- **Comprehensive coverage** of critical code quality aspects

code_review/- **Educational feedback** that helps developers improve their skills

├── context_analysis/          # Phase 1: Context & Architecture Review- **Efficient review process** with structured checklists and criteria

│   ├── README.md- **Standards alignment** with organizational coding guidelines

│   └── python_context_analysis.md

├── code_quality/              # Phase 2: Code Quality & Standards## 📁 Available Templates

│   ├── README.md

│   └── python_code_quality.md### Python Code Review Protocol

├── security_review/           # Phase 3: Security & Vulnerabilities**Location**: `python/`

│   ├── README.md

│   └── python_security_review.mdA comprehensive six-phase code review methodology specifically designed for Python applications, aligned with organizational coding standards.

├── performance_review/        # Phase 4: Performance & Optimization

│   ├── README.md**Phases:**

│   └── python_performance_review.md1. **Context & Architecture Review** - Project structure, documentation, and design

├── testing_review/            # Phase 5: Testing & Quality Assurance2. **Code Quality & Standards Review** - Style guidelines, formatting, and conventions

│   ├── README.md3. **Security & Error Handling Review** - Vulnerabilities, input validation, and error management

│   └── python_testing_review.md4. **Performance & Scalability Review** - Efficiency, optimization, and scale considerations

└── final_report/              # Phase 6: Final Report & Recommendations5. **Testing & Quality Assurance Review** - Test coverage, quality, and methodology

    ├── README.md6. **Final Review & Recommendations** - Synthesis, assessment, and action plan

    └── python_final_report.md

```**Features:**

- Copy-paste ready prompts for AI-assisted reviews

---- Detailed checklists for each phase

- Standards-based evaluation criteria

## 🎯 Purpose- Comprehensive README with step-by-step protocol

- Individual markdown files per phase for easy navigation

Standardized code review templates ensure:- Prioritized recommendations (Critical/High/Medium/Low)

- **Consistent review quality** across team members and projects

- **Comprehensive coverage** of critical code quality aspects**Time Investment:**

- **Educational feedback** that helps developers improve their skills- Quick Review: 1-2 hours (checklists only)

- **Efficient review process** with structured checklists and criteria- Standard Review: 3-4 hours (checklists + key prompts)

- **Standards alignment** with organizational coding guidelines- Deep Review: 5-6 hours (full protocol with AI assistance)



---**See**: [`python/README.md`](python/README.md) for complete details



## 📋 Review Phases---



### [Phase 1: Context Analysis & Initial Assessment](context_analysis/)## 🚀 Getting Started

**Objective**: Understand project purpose, architecture, and establish review priorities

### For Reviewers

**Python Templates**:

- [Python Context Analysis](context_analysis/python_context_analysis.md)1. **Select language/framework**: Navigate to appropriate directory (e.g., `python/`)

2. **Read the protocol**: Review the README for overview and methodology

**Time**: 1-2 hours  3. **Follow phases sequentially**: Work through each phase in order

**Key Activities**: Project assessment, architecture mapping, dependency analysis, review planning4. **Use checklists**: Verify compliance with each checklist item

5. **Copy prompts**: Use detailed prompts for AI-assisted analysis

---6. **Document findings**: Record issues with specific examples and locations

7. **Provide recommendations**: Prioritize findings and suggest remediation

### [Phase 2: Code Quality Review](code_quality/)

**Objective**: Evaluate code style, maintainability, documentation, and best practices### For Development Teams



**Python Templates**:1. **Pre-review preparation**: Update documentation, run tests, fix obvious issues

- [Python Code Quality Review](code_quality/python_code_quality.md)2. **Understand standards**: Familiarize with coding standards referenced in templates

3. **Be receptive**: Embrace feedback as learning opportunities

**Time**: 2-3 hours  4. **Discuss trade-offs**: Communicate constraints and decisions

**Key Activities**: Style compliance, naming conventions, code organization, complexity analysis, documentation review5. **Track remediation**: Create tickets and monitor progress

6. **Schedule follow-ups**: Plan re-reviews after addressing findings

---

## 🛠 Template Philosophy

### [Phase 3: Security Review](security_review/)

**Objective**: Identify vulnerabilities and security risks### Core Principles



**Python Templates**:- **Educational Approach**: Reviews teach "why," not just "what"

- [Python Security Review](security_review/python_security_review.md)- **Standards-Aligned**: Based on organizational coding standards

- **Actionable Feedback**: Specific recommendations with remediation steps

**Time**: 2-4 hours  - **Balanced Assessment**: Acknowledge strengths and improvements

**Key Activities**: OWASP Top 10 check, authentication review, input validation, data protection, dependency scanning- **AI-Assisted**: Prompts designed for use with AI coding assistants



---### Review Outcomes



### [Phase 4: Performance Review](performance_review/)Each review provides:

**Objective**: Evaluate performance and identify optimization opportunities- **Health Score**: Overall project assessment (1-5)

- **Deployment Recommendation**: Go/No-Go/Conditional decision

**Python Templates**:- **Prioritized Action Plan**: Issues categorized by severity

- [Python Performance Review](performance_review/python_performance_review.md)- **Technical Debt Quantification**: Effort estimates for improvements

- **Risk Assessment**: Identified risks with mitigation strategies

**Time**: 2-3 hours  

**Key Activities**: Bottleneck identification, algorithm analysis, database optimization, memory profiling, caching## 📈 Best Practices



---### Using the Templates



### [Phase 5: Testing Review](testing_review/)- **Follow phases sequentially** for comprehensive coverage

**Objective**: Assess test coverage, quality, and testing practices- **Use AI assistance** with provided prompts for efficiency

- **Validate AI findings** against actual code with human judgment

**Python Templates**:- **Document thoroughly** with specific examples and line numbers

- [Python Testing Review](testing_review/python_testing_review.md)- **Prioritize actionably** based on severity and impact

- **Balance critique and praise** to maintain team morale

**Time**: 1-2 hours  

**Key Activities**: Coverage assessment, test quality evaluation, edge case verification, mocking review### Customizing for Your Project



---- **Skip irrelevant phases** for focused reviews (e.g., security-only)

- **Adjust depth** based on available time and project criticality

### [Phase 6: Final Report & Recommendations](final_report/)- **Adapt criteria** to project-specific requirements

**Objective**: Consolidate findings and provide actionable recommendations- **Extend templates** with organization-specific checks

- **Track effectiveness** and refine based on outcomes

**Python Templates**:

- [Python Final Report](final_report/python_final_report.md)## 🔄 Continuous Improvement



**Time**: 1-2 hours  Templates evolve based on:

**Key Activities**: Finding consolidation, issue prioritization, improvement roadmap, executive summary- **Team feedback**: Input from reviewers and developers

- **Industry standards**: Updates to best practices

---- **Tool integration**: Enhancements for review workflows

- **Metric analysis**: Data-driven improvements

## ⏱️ Time Investment- **Lessons learned**: Real-world application insights



- **Quick Review**: 1-2 hours (Phase 1, 2, 6 checklists only)## 📝 Contributing

- **Standard Review**: 3-4 hours (Phases 1-3, 6 with key prompts)

- **Deep Review**: 5-6 hours (All phases with full AI assistance)To contribute improvements:

- **Comprehensive Review**: 9-16 hours (All phases with detailed analysis)1. **Test thoroughly**: Validate changes with actual reviews

2. **Document rationale**: Explain reasoning for modifications

---3. **Ensure consistency**: Maintain structure and format

4. **Share learnings**: Contribute insights from usage

## 🚀 Quick Start5. **Submit clearly**: Provide clear descriptions of changes



### For Reviewers## 🔧 Future Templates



1. **Select your language**: Choose the appropriate phase directoryPlanned additions:

2. **Start with Phase 1**: Understand context before diving into code- **JavaScript/TypeScript**: Frontend and Node.js applications

3. **Follow sequentially**: Work through phases in order for best results- **Java**: Enterprise application reviews

4. **Use the templates**: Copy prompts and checklists from markdown files- **C#/.NET**: Windows and enterprise applications

5. **Document findings**: Record specific examples and locations- **Go**: Microservices and cloud-native applications

6. **Complete Phase 6**: Consolidate into actionable report- **Rust**: Systems programming reviews



### For Development Teams---



1. **Prepare for review**: Update documentation, run tests, fix obvious issues*Last Updated: October 2025*

2. **Know the standards**: Review organizational coding guidelines*Current Templates: Python (complete)*
3. **Be open to feedback**: Treat reviews as learning opportunities
4. **Discuss constraints**: Communicate trade-offs and decisions
5. **Track remediation**: Create tickets and monitor progress
6. **Follow up**: Schedule re-review after addressing critical findings

---

## 🛠 Template Philosophy

### Core Principles

- **Educational Approach**: Reviews explain "why," not just "what"
- **Standards-Aligned**: Based on organizational coding standards
- **Actionable Feedback**: Specific recommendations with remediation steps
- **Balanced Assessment**: Acknowledge strengths alongside improvements
- **AI-Assisted**: Prompts designed for AI coding assistants

### Review Outcomes

Each complete review provides:
- **Health Score**: Overall project assessment (1-5 scale)
- **Deployment Recommendation**: Go/No-Go/Conditional decision
- **Prioritized Action Plan**: Issues categorized by severity (Critical/High/Medium/Low)
- **Technical Debt Quantification**: Effort estimates for improvements
- **Risk Assessment**: Identified risks with mitigation strategies

---

## 📈 Best Practices

### Effective Reviews

- **Follow phases sequentially** for comprehensive coverage
- **Use AI assistance** with provided prompts for efficiency
- **Validate AI findings** with human judgment
- **Document thoroughly** with specific examples and line numbers
- **Prioritize actionably** based on severity and impact
- **Balance critique and praise** to maintain team morale

### Customization

- **Skip irrelevant phases** for focused reviews (e.g., security-only)
- **Adjust depth** based on time and project criticality
- **Adapt criteria** to project-specific requirements
- **Extend templates** with organization-specific checks
- **Track effectiveness** and refine based on outcomes

---

## 🔧 Language Support

### Currently Available
- **Python**: Complete 6-phase methodology (all phases)

### Planned
- **JavaScript/TypeScript**: Frontend and Node.js applications
- **Java**: Enterprise application reviews
- **C#/.NET**: Windows and enterprise applications
- **Go**: Microservices and cloud-native applications
- **Rust**: Systems programming reviews

---

## 📝 Contributing

To contribute improvements:
1. **Test thoroughly**: Validate changes with actual reviews
2. **Document rationale**: Explain reasoning for modifications
3. **Maintain consistency**: Follow structure and format
4. **Share learnings**: Contribute insights from usage
5. **Submit clearly**: Provide clear descriptions of changes

---

*Last Updated: October 2025*  
*Current Templates: Python (6 phases complete)*

[↑ Back to Repository Root](../README.md)
