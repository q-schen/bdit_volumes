# Traffic Volumes Modelling Project

## 1. Purpose
Develop a methodology for estimating traffic volumes on road segments in the City of Toronto.

## 2. Introduction
The core mission of the City of Toronto's Big Data Innovation Team is to leverage emerging data sources and analytical techniques to advance the City's understanding of its transportation networks. This work involves, among other objectives, the production of indicative corridor-specific and city-wide performance metrics. These metrics are reliant on disaggregate data with spatial and temporal coverage that generally encompass two measures:

**1. Speed or Travel Times:** used as an indication of the road segment's performance; and

**2. Traffic Volumes:** used as a weighting measure when compiling aggregate metrics.

- Availability of volume data in City
- Need for volume profiles
- Toronto Centreline geometry
Volume data

The City of Toronto's traffic volume collection efforts can be broken into three (3) buckets:

**1. Permanent Traffic Counts:** Loop detectors, most of which are under the jurisdiction of the RESCU traffic management system and primarily cover the Gardiner Expressway, Don Valley Parkway, Lakeshore Boulevard and Allen Road.

**2. Short Period Traffic Counts (SPTCs):** Volumes collected using temporary automatic traffic recorders (ATRs), and typically carried out over 3 or 7-day periods. These are typically gathered to support specific studies by Transportation Services (e.g. signal retiming studies) or other divisions as well as through a City-run rotating count program.

**3. Turning Movement Counts (TMCs):** Volumes can be inferred using manual turning movement counts, although these typically do not cover a full 24-hour period and may have significant gaps given the manual nature of these counts.

## 3. Scope

- 

## 4. Project Tasks
**1. Map Artery Codes to Centreline:** Linking Artery Codes from the existing FLOW system to the City's Centreline shapefile, with additional descriptive fields (e.g. directionality) as necessary.

**2. Definition of Corridors:** Develop reproducible process for aggregating relevant centreline segments into corridors

**3. Literature Review:** Explore methods employed in other jurisdictions for interpolating or extrapolating traffic volumes both spatially and temporally, with a specific focus on cases where sparse counts exist. Produce summary of methods that may have value for this project for further exploration.

**4. Exploration of Methods:** Implement and compare methods deemed potentially feasible in *C.* to interpolating volumes on a subset of selected corridors.

**5. Data Harmonization (if necessary):**

**6. Model Development:**

**7. Model Validation:**

**8. Tool Deployment:**

## 5. Related Tasks
1. Explore the availability and value of alternative sources of volume data.
2. Develop process for identifying priority segments as candidates for the implementation of permanent and/or short period traffic count stations.