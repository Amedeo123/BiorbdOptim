import biorbd
from casadi import MX, vertcat

from .dynamics import Dynamics
from .mapping import BidirectionalMapping, Mapping


class ProblemType:
    """
    Includes methods suitable for several situations
    """

    @staticmethod
    def torque_driven(nlp):
        """
        Names states (nlp.x) and controls (nlp.u) and gives size to (nlp.nx) and (nlp.nu).
        Works with torques but without muscles, must be used with dynamics without contacts.
        :param nlp: An instance of the OptimalControlProgram class.
        """
        nlp["dynamics_func"] = Dynamics.forward_dynamics_torque_driven
        ProblemType.__configure_torque_driven(nlp)

    @staticmethod
    def torque_driven_with_contact(nlp):
        """
        Names states (nlp.x) and controls (nlp.u) and gives size to (nlp.nx) and (nlp.nu).
        Works with torques, without muscles, must be used with dynamics with contacts.
        :param nlp: An OptimalControlProgram class.
        """
        nlp["dynamics_func"] = Dynamics.forward_dynamics_torque_driven_with_contact
        ProblemType.__configure_torque_driven(nlp)

    @staticmethod
    def torque_driven_with_external_forces(nlp):
        nlp["f_ext"] = []
        nlp["dynamics_func"] = Dynamics.forward_dynamics_torque_driven_with_external_forces
        for external in nlp["forces_and_moments"]:
            m1, m2, m3 = biorbd.Scalar(external[0]), biorbd.Scalar(external[1]), biorbd.Scalar(external[2])
            f1, f2, f3 = biorbd.Scalar(external[3]), biorbd.Scalar(external[4]), biorbd.Scalar(external[5])
            nlp["f_ext"].append(biorbd.VecBiorbdSpatialVector([biorbd.SpatialVector(m1, m2, m3, f1, f2, f3)]))
        ProblemType.__configure_torque_driven(nlp)

    @staticmethod
    def __configure_torque_driven(nlp):
        """
        Configures common settings for torque driven problems with and without contacts.
        :param nlp: An OptimalControlProgram class.
        """
        if nlp["q_mapping"] is None:
            nlp["q_mapping"] = BidirectionalMapping(
                Mapping(range(nlp["model"].nbQ())), Mapping(range(nlp["model"].nbQ()))
            )
        if nlp["q_dot_mapping"] is None:
            nlp["q_dot_mapping"] = BidirectionalMapping(
                Mapping(range(nlp["model"].nbQdot())), Mapping(range(nlp["model"].nbQdot()))
            )
        if nlp["tau_mapping"] is None:
            nlp["tau_mapping"] = BidirectionalMapping(
                Mapping(range(nlp["model"].nbGeneralizedTorque())), Mapping(range(nlp["model"].nbGeneralizedTorque()))
            )

        dof_names = nlp["model"].nameDof()
        q = MX()
        q_dot = MX()
        for i in nlp["q_mapping"].reduce.map_idx:
            q = vertcat(q, MX.sym("Q_" + dof_names[i].to_string()))
        for i in nlp["q_dot_mapping"].reduce.map_idx:
            q_dot = vertcat(q_dot, MX.sym("Qdot_" + dof_names[i].to_string()))
        nlp["x"] = vertcat(q, q_dot)

        u = MX()
        for i in nlp["tau_mapping"].reduce.map_idx:
            u = vertcat(u, MX.sym("Tau_" + dof_names[i].to_string()))
        nlp["u"] = u
        nlp["nx"] = nlp["x"].rows()
        nlp["nu"] = nlp["u"].rows()

        nlp["nbQ"] = nlp["q_mapping"].reduce.len
        nlp["nbQdot"] = nlp["q_dot_mapping"].reduce.len
        nlp["nbTau"] = nlp["tau_mapping"].reduce.len

        nlp["has_states"] = {"q": nlp["q_mapping"].reduce.len, "q_dot": nlp["q_dot_mapping"].reduce.len}
        nlp["has_controls"] = {"tau": nlp["tau_mapping"].reduce.len}

    @staticmethod
    def muscle_activations_and_torque_driven(nlp):
        """
        Names states (nlp.x) and controls (nlp.u) and gives size to (nlp.nx) and (nlp.nu).
        Works with torques and muscles.
        :param nlp: An OptimalControlProgram class.
        """
        nlp["dynamics_func"] = Dynamics.forward_dynamics_torque_muscle_driven
        ProblemType.__configure_torque_driven(nlp)

        u = MX()
        nlp["nbMuscle"] = nlp["model"].nbMuscles()
        muscle_names = nlp["model"].muscleNames()
        for i in range(nlp["nbMuscle"]):
            u = vertcat(u, MX.sym("Muscle_" + muscle_names[i].to_string() + "_activation"))
        nlp["u"] = vertcat(nlp["u"], u)
        nlp["nu"] = nlp["u"].rows()

        nlp["has_controls"]["muscles"] = nlp["nbMuscle"]

    @staticmethod
    def muscle_excitations_and_torque_driven(nlp):
        """
        Names states (nlp.x) and controls (nlp.u) and gives size to (nlp.nx) and (nlp.nu).
        Works with torques and muscles.
        :param nlp: An OptimalControlProgram class.
        """
        nlp["dynamics_func"] = Dynamics.forward_dynamics_muscle_excitations_and_torque_driven
        ProblemType.__configure_torque_driven(nlp)

        u = MX()
        x = MX()
        nlp["nbMuscle"] = nlp["model"].nbMuscles()
        muscle_names = nlp["model"].muscleNames()
        for i in range(nlp["nbMuscle"]):
            u = vertcat(u, MX.sym("Muscle_" + muscle_names[i].to_string() + "_excitation"))
            x = vertcat(x, MX.sym("Muscle_" + muscle_names[i].to_string() + "_activation"))
        nlp["u"] = vertcat(nlp["u"], u)
        nlp["x"] = vertcat(nlp["x"], x)
        nlp["nu"] = nlp["u"].rows()
        nlp["nx"] = nlp["x"].rows()

        nlp["has_states"]["muscles"] = nlp["nbMuscle"]
        nlp["has_controls"]["muscles"] = nlp["nbMuscle"]

    @staticmethod
    def muscles_and_torque_driven_with_contact(nlp):
        """
        Names states (nlp.x) and controls (nlp.u) and gives size to (nlp.nx) and (nlp.nu).
        Works with torques and muscles.
        :param nlp: An OptimalControlProgram class.
        """
        nlp["dynamics_func"] = Dynamics.forward_dynamics_torque_muscle_driven_with_contact
        ProblemType.__configure_torque_driven(nlp)

        u = MX()
        nlp["nbMuscle"] = nlp["model"].nbMuscles()
        muscle_names = nlp["model"].muscleNames()
        for i in range(nlp["nbMuscle"]):
            u = vertcat(u, MX.sym("Muscle_" + muscle_names[i].to_string() + "_activation"))
        nlp["u"] = vertcat(nlp["u"], u)
        nlp["nu"] = nlp["u"].rows()

        nlp["has_controls"]["muscles"] = nlp["nbMuscle"]
