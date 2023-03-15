# Fox Capabilities
This module provide a capability permission system for Django. It is heavilly inspired
by [Capn'Proto documentation](https://capnproto.org) ([interesting paper](http://www.erights.org/elib/capability/ode/ode.pdf)).

Goal features:
- [] Local permission system: simplified permission system assuming database is a source of trust.
- [] External: through certificate chains of capabilities in references: signing and validating
- [] Rest API
- [] Class based views
- [] Extensible Agent allowing to sign and verify
- [] Authentication scheme that can be used in ActivityPub-like APIs.
- [] Test proofed
