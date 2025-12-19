# District Energy Model (DEM)

District Energy Model (DEM) is a Python-based multi-energy system model for simulating energy demand, generation, storage, and optimisation at the district and municipal scale with a focus on decentralised renewabl energy technologies.
The model is developed at [HSLU CC TES](https://www.hslu.ch/cctes) in the framework of the [SWEET EDGE](https://www.sweet-edge.ch/en/work-packages/wp-1) project.

---
## Documentation

Documentation is available on [Read The Docs](https://dem-documentation.readthedocs.io/en/latest/).


## Short Description

The District Energy Model (DEM) is a Python-based linear multi-energy system model designed to simulate energy flows at the district scale with hourly resolution. A “district” in this context can refer to anything from a small group of buildings to an entire municipality or city.

DEM combines building-level heat and electricity demand with aggregated energy generation, conversion, and storage technologies at the district level. Unlike many other tools, it does not rely on manual parameterization. Instead, the model automatically configures itself using publicly available data on buildings, energy resources, and existing energy systems. This allows simulations to be performed for any Swiss municipality without requiring additional local data.

The typical workflow consists of:

1) Automatic collection of climate, building, and technology data for the selected district or buildings.

2) User specification of the technology scope (e.g., generation, conversion, storage) and adjustment of key parameters such as efficiency or capacity.

3) Scenario definition.

4) Simulation of energy balances.

5) Generation of outputs for analysis.

In addition to simulation, DEM also supports MILP optimization of design and operation.


## License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.