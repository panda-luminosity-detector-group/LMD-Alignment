#include "Mille.h"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <numeric>

struct Point3D {
  double X;
  double Y;
  double Z;

  std::string toString() const {
    return "[" + std::to_string(X) + ", " + std::to_string(Y) + ", " +
           std::to_string(Z) + "]";
  }
};

struct StraightTrack {
  Point3D Origin;
  Point3D Direction;
};

struct MilleData {
  float Residual;
  float Sigma;
  std::vector<float> LocalParameterDerivatives;
  std::vector<float> GlobalParameterDerivatives;
};

std::vector<MilleData> convertData(const std::vector<Point3D> &RecoHits,
                                   const StraightTrack &Track) {
  std::vector<MilleData> Data;
  MilleData x;
  // TODO: calculate the track derivatives here
  // x.Residual = 1.0;
  // x.Sigma = 0.001;
  // x.LocalParameterDerivatives.push_back(0.1);
  // x.GlobalParameterDerivatives.push_back(0.1);
  Data.push_back(x);
  return Data;
}

namespace py = pybind11;

PYBIND11_MODULE(pyMille, m) {
  m.doc() = "pybind11 Python interface for Millepede II";

  py::class_<Point3D>(m, "Point3D")
      .def(py::init<>())
      .def(py::init<double, double, double>())
      .def_readwrite("x", &Point3D::X)
      .def_readwrite("y", &Point3D::Y)
      .def_readwrite("z", &Point3D::Z)
      .def("__repr__", &Point3D::toString);

  py::class_<StraightTrack>(m, "StraightTrack")
      .def(py::init<>())
      .def(py::init<Point3D, Point3D>())
      .def_readwrite("origin", &StraightTrack::Origin)
      .def_readwrite("direction", &StraightTrack::Direction)
      .def("__repr__", [](const StraightTrack &Track) {
        return "origin: " + Track.Origin.toString() +
               "\ndirection: " + Track.Direction.toString() + "\n";
      });

  py::class_<Mille>(m, "Mille")
      .def(py::init<const char *, bool, bool>(), py::arg("output_filename"),
           py::arg("as_binary") = true, py::arg("write_zero") = false)
      .def("write_event",
           [](Mille &MilleInstance, const std::vector<Point3D> &RecoHits,
              const StraightTrack &Track) {
             auto AllMilleData = convertData(RecoHits, Track);
             for (auto const &x : AllMilleData) {
               if (x.LocalParameterDerivatives.size() > 0 &&
                   x.GlobalParameterDerivatives.size() > 0) {
                 std::vector<int> labels(x.GlobalParameterDerivatives.size());
                 std::iota(labels.begin(), labels.end(), 1);
                 MilleInstance.mille(x.LocalParameterDerivatives.size(),
                                     &x.LocalParameterDerivatives[0],
                                     x.GlobalParameterDerivatives.size(),
                                     &x.GlobalParameterDerivatives[0],
                                     &labels[0], x.Residual, x.Sigma);
               }
             }
             MilleInstance.end();
           });
}