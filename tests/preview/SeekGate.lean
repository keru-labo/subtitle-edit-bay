structure Gate where
  generation : Nat := 0
  dispatched : Nat := 0
  pending : Option Nat := none

def request (s : Gate) : Gate :=
  { s with generation := s.generation + 1, pending := some (s.generation + 1) }

def dispatch (s : Gate) : Gate :=
  match s.pending with
  | none => s
  | some token => { s with dispatched := token, pending := none }

def invalidate (s : Gate) : Gate :=
  { s with generation := s.generation + 1, pending := none }

def MayPublish (s : Gate) (token : Nat) : Prop :=
  token ≠ 0 ∧ token = s.generation ∧ token = s.dispatched

theorem older_never_publishes (s : Gate) (token : Nat)
    (older : token < s.generation) : ¬ MayPublish s token := by
  intro h
  exact (Nat.ne_of_lt older) h.2.1

theorem superseded_never_publishes (s : Gate) :
    ¬ MayPublish (request s) s.generation := by
  intro h
  have eq := h.2.1
  simp [request] at eq

theorem latest_dispatch_publishes (s : Gate) :
    MayPublish (dispatch (request (request s))) (s.generation + 2) := by
  simp [MayPublish, dispatch, request, Nat.add_assoc]

theorem invalidation_drops_pending (s : Gate) :
    (dispatch (invalidate s)).pending = none := by
  rfl

theorem invalidation_rejects_previous (s : Gate) :
    ¬ MayPublish (invalidate s) s.generation := by
  intro h
  have eq := h.2.1
  simp [invalidate] at eq
