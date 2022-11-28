#include "Mille.h"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <numeric>

namespace py = pybind11;

PYBIND11_MODULE(pyMille, m) {
  m.doc() = "pybind11 Python interface for Millepede II";

  py::class_<Mille>(m, "Mille")
      .def(py::init<const char *, bool, bool>(), py::arg("output_filename"),
           py::arg("as_binary") = true, py::arg("write_zero") = false)
      .def("write",
           [](Mille &MilleInstance,
              const std::vector<float> &LocalParameterDerivatives,
              const std::vector<float> &GlobalParameterDerivatives,
              const std::vector<int> &Labels,
              float Residual, float Sigma) {
             if (LocalParameterDerivatives.size() > 0 &&
                 GlobalParameterDerivatives.size() > 0 &&
                 Labels.size() == GlobalParameterDerivatives.size()) {
               //std::vector<int> labels(GlobalParameterDerivatives.size());
               //std::iota(labels.begin(), labels.end(), 1);
               MilleInstance.mille(LocalParameterDerivatives.size(),
                                   LocalParameterDerivatives.data(),
                                   GlobalParameterDerivatives.size(),
                                   GlobalParameterDerivatives.data(),
                                   Labels.data(),
                                   Residual, Sigma);
             }
           },
           "Write data to the mille output file.",
           py::arg("local_parameter_derivatives"),
           py::arg("global_parameter_derivatives"),
           py::arg("labels"),
           py::arg("residual"),
           py::arg("sigma"))
      .def("end", &Mille::end);

}