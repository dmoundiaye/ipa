from dataclasses import dataclass

@dataclass
class interface:
    nom: str
    status: str="down"
    vlan: int | None =None

etho=interface(nom="gigabitEthernet0/0", status="up", vlan=13)

print(etho)
