# USDM_v4.0.0 generation report

Generated 2026-11-05

| | |
|---|---|
| OpenAPI specification | docs/ddf_ra/USDM_API.yaml |
| UML model | input/v4.0.0/v4.0.0_USDM_UML.qea |
| Controlled terminology | input/v4.0.0/v4.0.0_USDM_CT.xlsx |
| Output directory | docs/releases |
| Generated | workbook, linkml |

## Summary

| Level | Section | Count |
|---|---|---|
| warning | UML: connectors skipped (source object not found) | 7 |
| warning | Workbook: classes omitted (not in the CT) | 2 |
| warning | CT: attributes and relationships with no CT entry | 16 |
| warning | Cardinality: OpenAPI minItems missing for UML lower bound | 13 |
| info | API-only relationships added from the OpenAPI specification | 14 |

**0 error(s), 38 warning(s), 14 note(s)**

## Warnings

### UML: connectors skipped (source object not found) (7)

- connector 3 (Association hasVersion) from object 0
- connector 9 (Association studyCells) from object 0
- connector 63 (Association) from object 0
- connector 64 (Association studyElements) from object 0
- connector 67 (Association) from object 0
- connector 109 (Association timelineExit) from object 0
- connector 348 (Association notes) from object 0

### Workbook: classes omitted (not in the CT) (2)

- ExtensionClass
- ExtensionAttribute

### CT: attributes and relationships with no CT entry (16)

- StudyVersion.eligibilityCriterionItems
- StudyVersion.narrativeContentItems
- StudyVersion.roles
- StudyVersion.organizations
- StudyVersion.studyInterventions
- StudyVersion.administrableProducts
- StudyVersion.medicalDevices
- StudyVersion.productOrganizationRoles
- StudyVersion.biomedicalConcepts
- StudyVersion.bcCategories
- StudyVersion.bcSurrogates
- StudyVersion.dictionaries
- StudyVersion.conditions
- StudyDesign.analysisPopulations
- InterventionalStudyDesign.analysisPopulations
- ObservationalStudyDesign.analysisPopulations

### Cardinality: OpenAPI minItems missing for UML lower bound (13)

- Estimand.intercurrentEvents: UML 1..*
- Estimand.interventionIds (UML interventions): UML 1..*
- ExtensionClass.extensionAttributes: UML 1..*
- GovernanceDate.geographicScopes: UML 1..*
- ScheduledDecisionInstance.conditionAssignments: UML 1..*
- StudyAmendment.changes: UML 1..*
- StudyAmendment.geographicScopes: UML 1..*
- StudyCell.elementIds (UML elements): UML 1..*
- StudyChange.changedSections: UML 1..*
- StudyVersion.studyIdentifiers: UML 1..*
- StudyVersion.titles: UML 1..*
- Substance.strengths: UML 1..*
- SyntaxTemplateDictionary.parameterMaps: UML 1..*

## Notes

### API-only relationships added from the OpenAPI specification (14)

- StudyVersion.eligibilityCriterionItems -> EligibilityCriterionItem (0..*)
- StudyVersion.narrativeContentItems -> NarrativeContentItem (0..*)
- StudyVersion.roles -> StudyRole (0..*)
- StudyVersion.organizations -> Organization (0..*)
- StudyVersion.studyInterventions -> StudyIntervention (0..*)
- StudyVersion.administrableProducts -> AdministrableProduct (0..*)
- StudyVersion.medicalDevices -> MedicalDevice (0..*)
- StudyVersion.productOrganizationRoles -> ProductOrganizationRole (0..*)
- StudyVersion.biomedicalConcepts -> BiomedicalConcept (0..*)
- StudyVersion.bcCategories -> BiomedicalConceptCategory (0..*)
- StudyVersion.bcSurrogates -> BiomedicalConceptSurrogate (0..*)
- StudyVersion.dictionaries -> SyntaxTemplateDictionary (0..*)
- StudyVersion.conditions -> Condition (0..*)
- StudyDesign.analysisPopulations -> AnalysisPopulation (0..*)
