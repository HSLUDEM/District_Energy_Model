---
title: 'District Energy Model (DEM): A Python framework for modelling renewable energy integration and flexibility at district scale.'
tags:
  - Python
  - Optimisation
  - multi-energy system
  - scenario analysis
  - renewable integration
authors:
  - name: Ueli Schilt
    orcid: 0000-0002-6104-1389
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Pascal M. Vecsei
    orcid: 0000-0003-1058-8808
    affiliation: 1
  - name: Somesh Vijayananda
    orcid: 0009-0009-4558-7064
    affiliation: 1
  - name: Philipp Schuetz
    orcid: 0000-0001-7564-1468
    affiliation: 1
	
affiliations:
 - name: Competence Centre for Thermal Energy Storage, School of Engineering and Architecture, Lucerne University of Applied Sciences, Horw, Switzerland
   index: 1
 - name: School of Architecture, Civil and Environmental Engineering, École Polytechnique Fédérale de Lausanne (EPFL), Lausanne, Switzerland
   index: 2
   
date: 24 November 2025
bibliography: paper.bib

---

# Summary

The transition to locally generated, decentralised, and renewable energy technologies is a promising pathway toward net-zero emissions and a decarbonised energy system. This transition requires systematic evaluation of potential future scenarios for technology adoption across multiple spatial scales. Computational energy system models are used for this purpose. The *District Energy Model (DEM)* is a Python-based multi-energy system model designed to simulate scenarios from the neighbourhood to the regional scale, with a focus on the integration of decentralised renewable energy technologies such as solar, wind, and biomass. DEM can be used to execute simulation and optimisation studies at hourly resolution using a snapshot-year methodology. It is released as an open-source Python library on [PyPi](https://pypi.org/project/district-energy-model/). The model can be launched via a command-line interface, not requiring any Python programming knowledge. Alternatively, it can be accessed programmatically through Python.
DEM requires two types of input: *configuration files* and *data files*. *Configuration files* specify the simulation settings (e.g., included buildings, temporal scope, output variables) and define the energy system configuration (e.g., scenarios, technologies, selected year). These configuration files are provided in YAML format [@benkiki2009yaml]. Configuration parameters may also be passed directly to DEM in Python. *Data files* contain model data such as energy demand profiles, generation potentials, and ambient conditions. They are provided in Apache Feather format [@apache2025feather]. For selected regions, these data files have been pre-compiled from public datasets and made available in a public repository, providing a fully parameterised model without requiring users to source or preprocess data. For example, data for a full parameterisation of DEM is available for all municipalities in Switzerland.

DEM comes with a detailed [documentation](https://dem-documentation.readthedocs.io/en/latest/), which includes step-by-step instructions, descriptions of modelling approaches and methods, and links to related publications and research.

# Statement of need

Several countries have defined national net-zero emission targets [@ipcc_climate_2023]. Switzerland, for example, aims to reach net-zero by 2050 [@switzerland2025_lts]. Achieving such targets generally requires a structural shift from large, centralised generation to decentralised renewable resources, including solar, wind, and biomass [@trutnevyte_renewable_2024; @van_liedekerke_renewable_2025]. To support energy system planning and policy design, scenario evaluation must be carried out at local scales such as districts, municipalities, cities, or similarly sized regions. This includes analysing system-integrated deployment of renewable energy generation, conversion, and storage technologies, assessing alternative demand trajectories, and identifying solutions optimised for specific objectives such as cost, emissions, or security of supply.

DEM provides these functions with a specific focus on the use of local renewable energy resources and the integration of decentralised technologies within local system boundaries. Multiple energy system and demand scenarios can be defined, simulated, and compared. Increased penetration of variable, distributed resources raises the relevance of supply- and demand-side flexibility [@kachirayil2022; @golmohamadi2024]. DEM models several flexibility options, including flexible electric vehicle charging, thermal and electrical storage, photovoltaic curtailment, and sector-coupling. 

Existing multi-energy system models have been applied extensively in case studies of local energy scenarios, but they typically target a single location. Each new application requires reparameterisation and new data collection, including demand profiles, cost estimates, and technology characteristics. Data acquisition and preparation dominate the modelling workload in such studies. DEM removes this burden for selected regions by providing pre-compiled and pre-processed datasets assembled from public sources. Simulation and optimisation studies can therefore be executed with minimal configuration (e.g., selecting the buildings to include) while maintaining full flexibility to replace any pre-configured dataset with user-defined data when required. For regions not included in the provided dataset, users can construct the necessary data using the specifications provided in the documentation. DEM’s input data architecture allows datasets to be provided at a large regional scale (e.g., an entire country) that can then be used to run simulations on any spatial subset of that data, such as individual municipalities or districts.

Optimisation is optional in DEM. Many scenario questions, such as assessing the impact of a specific technology, do not require optimisation because the system configuration is fixed, the technology capacities are predetermined, or the aim is to examine feasibility, energy balances, or system interactions rather than to identify an optimal design. Simulation is also appropriate when the objective is to reproduce prescribed operating behaviour, when data are insufficient to support a reliable optimisation formulation, or when the computational burden of optimisation is unjustified for large scenario ensembles. In these cases, DEM runs simulations without invoking the optimisation module, yielding short computation times and direct results. This distinguishes DEM from optimisation-centric energy system models that rely exclusively on optimisation and therefore cannot execute non-optimised scenario analyses with fixed configurations or purely exploratory simulations.

Initially developed within the framework of a research project, DEM is designed for a diverse target audience extending from academia and research projects to decision-makers in municipalities, energy utilities, and the industrial sector.

# Modelling approach

DEM simulates energy flows within a defined district using a hybrid bottom-up and top-down modelling approach. A “district” can represent any spatial scale, from a small group of buildings to an entire municipality or city. Building-level attributes are modelled individually (e.g., type, location, size, age, heat and electricity demand, heating system, and on-site solar potential). Other parameters are defined at district scale, including wind and biomass resources, ambient conditions, and mobility demand. Each simulation is constructed from three elements: a set of available resources (e.g., wind, solar, biomass, hydro), a set of technologies for generation, conversion, and storage, and a set of demand profiles for heat, electricity, and mobility. These elements interact through defined flows of resources and energy carriers such as electricity and heat. An example system layout is shown in \autoref{fig:dem_layout}. DEM imposes no fixed limit on the number of buildings included, allowing customised definitions of district boundaries and building selections.

The workflow consists of: (1) input-data collection; (2) model parameterisation and configuration; (3) scenario generation; (4a) simulation; (4b) optimisation (optional); (5) output generation.

The optimisation module in DEM is implemented using the Calliope framework [@pfenningerCalliope2018a], which is based on the Pyomo optimisation programming environment [@hart2011pyomo].

![Schematic of an exemplary district energy system showing resources, generation, conversion, and storage technologies, and associated heat, electricity, and mobility demands. DEM supports many more technologies and scenarios than those illustrated here, as detailed in the [documentation](https://dem-documentation.readthedocs.io/en/latest/). \label{fig:dem_layout}]( dem_example_layout_v2.png){ width=100% }

# Acknowledgements
The development of DEM was carried out within the *Competence Centre Thermal Energy Storage* (CC TES) at *Lucerne University of Applied Sciences and Arts* (HSLU). The research published in this publication was carried out with the support of the Swiss Federal Office of Energy as part of the SWEET consortium EDGE. The authors bear sole responsibility for the conclusions and the results presented in this publication.



# References